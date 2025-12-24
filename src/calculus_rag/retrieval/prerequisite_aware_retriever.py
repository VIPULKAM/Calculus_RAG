"""
Prerequisite-aware retrieval for calculus RAG.

Enhances retrieval by also fetching content from prerequisite topics,
helping students get foundational context for their questions.

Supports both standard semantic search and hybrid (semantic + keyword) search.
"""

from dataclasses import dataclass
from typing import Any

from calculus_rag.embeddings.base import BaseEmbedder
from calculus_rag.prerequisites.detector import GapDetector
from calculus_rag.prerequisites.graph import PrerequisiteGraph
from calculus_rag.prerequisites.topics import build_prerequisite_graph, get_topic_info
from calculus_rag.retrieval.retriever import Retriever, RetrievalResult
from calculus_rag.utils.text_cleanup import cleanup_math_text
from calculus_rag.vectorstore.base import BaseVectorStore
from calculus_rag.vectorstore.pgvector_store import PgVectorStore


@dataclass
class PrerequisiteAwareResult:
    """
    Result from prerequisite-aware retrieval.

    Attributes:
        results: Combined retrieval results (main + prerequisite content).
        detected_topic: The topic detected from the query.
        prerequisites_used: List of prerequisite topics that were searched.
        main_results_count: Number of results from the main topic.
        prerequisite_results_count: Number of results from prerequisites.
    """

    results: list[RetrievalResult]
    detected_topic: str | None
    prerequisites_used: list[str]
    main_results_count: int
    prerequisite_results_count: int


class PrerequisiteAwareRetriever:
    """
    Retriever that fetches content from both the main topic and its prerequisites.

    This helps students get foundational context alongside the main answer.

    Example:
        >>> retriever = PrerequisiteAwareRetriever(embedder, vector_store)
        >>> result = await retriever.retrieve("Explain the chain rule")
        >>> # Returns content about chain rule AND function composition (prerequisite)
        >>> print(f"Main: {result.main_results_count}, Prereqs: {result.prerequisite_results_count}")
    """

    def __init__(
        self,
        embedder: BaseEmbedder,
        vector_store: BaseVectorStore,
        prerequisite_graph: PrerequisiteGraph | None = None,
        max_prerequisite_depth: int = 2,
        prerequisite_weight: float = 0.7,
        use_hybrid_search: bool = True,
        semantic_weight: float = 0.7,
    ) -> None:
        """
        Initialize the prerequisite-aware retriever.

        Args:
            embedder: The embedding model for encoding queries.
            vector_store: The vector store containing document chunks.
            prerequisite_graph: Optional custom prerequisite graph.
                               If None, builds from default topics.
            max_prerequisite_depth: Maximum depth of prerequisites to include.
                                   1 = direct prerequisites only.
                                   2 = prerequisites and their prerequisites.
            prerequisite_weight: Score weight for prerequisite results (0-1).
                                Main topic results keep full score.
            use_hybrid_search: Whether to use hybrid (semantic + keyword) search.
            semantic_weight: Weight for semantic search in hybrid mode (0-1).
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.base_retriever = Retriever(embedder, vector_store)
        self.graph = prerequisite_graph or build_prerequisite_graph()
        self.detector = GapDetector(self.graph)
        self.max_prerequisite_depth = max_prerequisite_depth
        self.prerequisite_weight = prerequisite_weight
        self.use_hybrid_search = use_hybrid_search
        self.semantic_weight = semantic_weight

    def _get_limited_prerequisites(self, topic: str, depth: int = 1) -> list[str]:
        """
        Get prerequisites up to a certain depth.

        Args:
            topic: The main topic.
            depth: How deep to traverse (1 = direct only).

        Returns:
            List of prerequisite topic IDs.
        """
        if depth <= 0:
            return []

        direct_prereqs = self.graph.get_prerequisites(topic)

        if depth == 1:
            return direct_prereqs

        # Get deeper prerequisites
        all_prereqs = set(direct_prereqs)
        for prereq in direct_prereqs:
            deeper = self._get_limited_prerequisites(prereq, depth - 1)
            all_prereqs.update(deeper)

        return list(all_prereqs)

    async def retrieve(
        self,
        query: str,
        n_results: int = 5,
        n_prerequisite_results: int = 2,
        filters: dict[str, Any] | None = None,
        include_prerequisites: bool = True,
    ) -> PrerequisiteAwareResult:
        """
        Retrieve content with prerequisite awareness.

        Args:
            query: The user's question.
            n_results: Number of main results to retrieve.
            n_prerequisite_results: Number of results per prerequisite topic.
            filters: Optional metadata filters.
            include_prerequisites: Whether to include prerequisite content.

        Returns:
            PrerequisiteAwareResult: Combined results with metadata.
        """
        # Step 1: Detect topic from query
        detected_topic = self.detector.analyze_query(query)

        # Minimum score threshold to filter out irrelevant chunks
        min_score = 0.45

        # Step 2: Get main results (hybrid or semantic search)
        if self.use_hybrid_search and isinstance(self.vector_store, PgVectorStore):
            # Use hybrid search for better keyword + semantic matching
            query_embedding = self.embedder.embed(query)
            hybrid_results = await self.vector_store.hybrid_search(
                query_text=query,
                query_embedding=query_embedding,
                n_results=n_results * 2,  # Get extra to account for filtering
                semantic_weight=self.semantic_weight,
                where=filters,
            )
            # Filter by minimum score, clean content, and convert to RetrievalResult
            main_results = [
                RetrievalResult(
                    content=cleanup_math_text(r.content),
                    score=r.score,
                    metadata=r.metadata,
                    chunk_id=r.id,
                )
                for r in hybrid_results
                if r.score >= min_score
            ][:n_results]
        else:
            # Fallback to standard semantic search (already has min_score filter)
            main_results = await self.base_retriever.retrieve(
                query=query,
                n_results=n_results,
                filters=filters,
                min_score=min_score,
            )

        prerequisites_used = []
        prerequisite_results = []

        # Step 3: Get prerequisite results if topic detected
        if include_prerequisites and detected_topic:
            # Get prerequisites up to configured depth
            prerequisites = self._get_limited_prerequisites(
                detected_topic, self.max_prerequisite_depth
            )

            for prereq_topic in prerequisites:
                # Get topic info for display name
                topic_info = get_topic_info(prereq_topic)

                if topic_info:
                    prerequisites_used.append(prereq_topic)

                    # Retrieve from this prerequisite topic
                    # Use topic name + query for better relevance
                    prereq_query = f"{topic_info['display_name']}: {query}"

                    prereq_results = await self.base_retriever.retrieve(
                        query=prereq_query,
                        n_results=n_prerequisite_results,
                        filters={"topic": prereq_topic} if filters is None else {**filters, "topic": prereq_topic},
                    )

                    # Weight down prerequisite scores
                    for result in prereq_results:
                        result.score *= self.prerequisite_weight
                        # Mark as prerequisite content
                        result.metadata["is_prerequisite"] = True
                        result.metadata["prerequisite_for"] = detected_topic

                    prerequisite_results.extend(prereq_results)

        # Step 4: Merge and sort results
        all_results = main_results + prerequisite_results

        # Remove duplicates (by chunk_id), keeping higher scores
        seen_ids = {}
        for result in all_results:
            if result.chunk_id not in seen_ids or result.score > seen_ids[result.chunk_id].score:
                seen_ids[result.chunk_id] = result

        unique_results = list(seen_ids.values())

        # Sort by score (descending)
        unique_results.sort(key=lambda r: r.score, reverse=True)

        return PrerequisiteAwareResult(
            results=unique_results,
            detected_topic=detected_topic,
            prerequisites_used=prerequisites_used,
            main_results_count=len(main_results),
            prerequisite_results_count=len(prerequisite_results),
        )

    async def retrieve_with_learning_path(
        self,
        query: str,
        completed_topics: set[str] | None = None,
        n_results: int = 5,
    ) -> tuple[PrerequisiteAwareResult, list[str]]:
        """
        Retrieve content and suggest a learning path for missing prerequisites.

        Args:
            query: The user's question.
            completed_topics: Topics the student has already mastered.
            n_results: Number of results to retrieve.

        Returns:
            Tuple of (retrieval results, suggested learning path).
        """
        completed = completed_topics or set()

        # Get retrieval results
        result = await self.retrieve(query, n_results=n_results)

        # Get learning path if topic detected
        learning_path = []
        if result.detected_topic:
            learning_path = self.graph.get_learning_path(
                result.detected_topic, completed
            )

        return result, learning_path

    def __repr__(self) -> str:
        return (
            f"PrerequisiteAwareRetriever("
            f"depth={self.max_prerequisite_depth}, "
            f"weight={self.prerequisite_weight})"
        )
