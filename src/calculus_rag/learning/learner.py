"""
Knowledge Learner - Save verified LLM responses to the knowledge base.

When the RAG system can't find good sources but the LLM provides a correct
answer (verified by user thumbs up), this module saves that knowledge for
future retrieval.
"""

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from calculus_rag.embeddings.base import BaseEmbedder
from calculus_rag.vectorstore.base import BaseVectorStore


@dataclass
class LearnedContent:
    """Represents content learned from LLM responses."""

    question: str
    answer: str
    topic: str | None = None
    chunk_id: str | None = None
    created_at: datetime | None = None


class KnowledgeLearner:
    """
    Learns from verified LLM responses and adds them to the knowledge base.

    When users confirm an LLM response is correct (thumbs up), this class:
    1. Checks for duplicate/similar content (deduplication)
    2. Formats the Q&A as a knowledge chunk
    3. Generates an embedding
    4. Stores it in the vector store with "learned" metadata

    Example:
        >>> learner = KnowledgeLearner(embedder, vector_store)
        >>> result = await learner.learn(
        ...     question="What is the derivative of sin(x)?",
        ...     answer="The derivative of sin(x) is cos(x).",
        ...     topic="derivatives.trig"
        ... )
        >>> if result.chunk_id:
        ...     print(f"Learned content saved as {result.chunk_id}")
        >>> else:
        ...     print("Skipped - similar content already exists")
    """

    def __init__(
        self,
        embedder: BaseEmbedder,
        vector_store: BaseVectorStore,
        min_answer_length: int = 50,
        similarity_threshold: float = 0.85,
    ) -> None:
        """
        Initialize the knowledge learner.

        Args:
            embedder: Embedding model for generating vectors.
            vector_store: Vector store to save learned content.
            min_answer_length: Minimum answer length to save (filters trivial answers).
            similarity_threshold: Skip saving if existing content similarity exceeds this (0-1).
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.min_answer_length = min_answer_length
        self.similarity_threshold = similarity_threshold

    def _generate_chunk_id(self, question: str, answer: str) -> str:
        """Generate a unique ID for the learned chunk."""
        content = f"{question}:{answer}"
        hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"learned_{hash_val}"

    def _format_as_markdown(self, question: str, answer: str, topic: str | None) -> str:
        """
        Format Q&A as markdown content for storage.

        Args:
            question: The user's question.
            answer: The LLM's verified answer.
            topic: Optional topic classification.

        Returns:
            Formatted markdown content.
        """
        # Clean up the answer (remove any system artifacts)
        clean_answer = answer.strip()

        # Build markdown content
        lines = []

        if topic:
            # Convert topic ID to readable title
            topic_title = topic.replace("_", " ").replace(".", " - ").title()
            lines.append(f"## {topic_title}")
            lines.append("")

        lines.append(f"**Question:** {question}")
        lines.append("")
        lines.append(f"**Answer:**")
        lines.append("")
        lines.append(clean_answer)

        return "\n".join(lines)

    def _detect_topic(self, question: str, answer: str) -> str | None:
        """
        Attempt to detect the calculus topic from the Q&A content.

        Args:
            question: The user's question.
            answer: The LLM's answer.

        Returns:
            Detected topic ID or None.
        """
        text = f"{question} {answer}".lower()

        # Topic detection patterns
        topic_patterns = {
            "derivatives.chain_rule": r"chain\s*rule",
            "derivatives.product_rule": r"product\s*rule",
            "derivatives.quotient_rule": r"quotient\s*rule",
            "derivatives.power_rule": r"power\s*rule",
            "derivatives.trig": r"derivative.*(sin|cos|tan|sec|csc|cot)",
            "derivatives.exponential": r"derivative.*(e\^|exp|logarithm|ln)",
            "derivatives.implicit": r"implicit\s*differentiation",
            "integration.substitution": r"(u[- ]substitution|substitution\s*method)",
            "integration.by_parts": r"integration\s*by\s*parts",
            "integration.partial_fractions": r"partial\s*fractions",
            "integration.definite": r"definite\s*integral",
            "integration.indefinite": r"indefinite\s*integral",
            "limits.definition": r"(limit\s*definition|epsilon[- ]delta)",
            "limits.lhopital": r"l'?h[oô]pital",
            "limits.continuity": r"continuity|continuous",
            "applications.optimization": r"(optimi[zs]ation|maximum|minimum)",
            "applications.related_rates": r"related\s*rates",
            "applications.area": r"area\s*(under|between)",
        }

        for topic_id, pattern in topic_patterns.items():
            if re.search(pattern, text):
                return topic_id

        # Broader category detection
        if "derivative" in text or "differentiat" in text:
            return "derivatives.basic"
        if "integral" in text or "antiderivative" in text:
            return "integration.basic"
        if "limit" in text:
            return "limits.basic"

        return None

    def _estimate_difficulty(self, question: str, answer: str) -> int:
        """
        Estimate difficulty level (1-5) from content complexity.

        Args:
            question: The user's question.
            answer: The LLM's answer.

        Returns:
            Difficulty level 1-5.
        """
        text = f"{question} {answer}".lower()

        # Complexity indicators
        advanced_patterns = [
            r"proof",
            r"theorem",
            r"epsilon[- ]delta",
            r"riemann",
            r"convergence",
            r"taylor\s*series",
            r"maclaurin",
            r"improper\s*integral",
        ]

        intermediate_patterns = [
            r"chain\s*rule",
            r"integration\s*by\s*parts",
            r"partial\s*fractions",
            r"implicit",
            r"related\s*rates",
            r"optimization",
        ]

        # Count complexity indicators
        advanced_count = sum(1 for p in advanced_patterns if re.search(p, text))
        intermediate_count = sum(1 for p in intermediate_patterns if re.search(p, text))

        if advanced_count >= 2:
            return 5
        if advanced_count >= 1:
            return 4
        if intermediate_count >= 2:
            return 4
        if intermediate_count >= 1:
            return 3

        # Default to moderate difficulty
        return 2

    async def _check_duplicate(self, embedding: list[float], question: str) -> tuple[bool, str | None]:
        """
        Check if similar content already exists in the knowledge base.

        Args:
            embedding: The embedding of the new content.
            question: The question to check for exact matches.

        Returns:
            Tuple of (is_duplicate, existing_chunk_id or None).
        """
        # Search for similar content
        results = await self.vector_store.query(
            query_embedding=embedding,
            n_results=3,
        )

        for result in results:
            # Check similarity threshold
            if result.score >= self.similarity_threshold:
                return True, result.id

            # Also check if it's learned content with same/similar question
            if result.metadata.get("source") == "learned_from_llm":
                orig_question = result.metadata.get("original_question", "")
                # Fuzzy match on question (lowercase, stripped)
                if orig_question.lower().strip() == question.lower().strip():
                    return True, result.id

        return False, None

    async def learn(
        self,
        question: str,
        answer: str,
        topic: str | None = None,
        detected_topic: str | None = None,
        source_scores: list[float] | None = None,
    ) -> LearnedContent:
        """
        Save a verified Q&A pair to the knowledge base.

        Includes deduplication: if similar content already exists (similarity > threshold),
        the save is skipped and the existing chunk info is returned.

        Args:
            question: The user's original question.
            answer: The LLM's verified answer.
            topic: Optional topic override.
            detected_topic: Topic detected during retrieval.
            source_scores: Original retrieval scores (for metadata).

        Returns:
            LearnedContent with the saved chunk details.
            If duplicate detected, chunk_id will be prefixed with "existing_".

        Raises:
            ValueError: If answer is too short or empty.
        """
        # Validate input
        if not answer or len(answer.strip()) < self.min_answer_length:
            raise ValueError(
                f"Answer too short (min {self.min_answer_length} chars). "
                "Only save substantial answers."
            )

        # Detect or use provided topic
        final_topic = topic or detected_topic or self._detect_topic(question, answer)

        # Create embedding FIRST for deduplication check
        embed_text = f"Question: {question}\n\nAnswer: {answer}"
        embedding = self.embedder.embed(embed_text)

        # Check for duplicates
        is_duplicate, existing_id = await self._check_duplicate(embedding, question)
        if is_duplicate:
            return LearnedContent(
                question=question,
                answer=answer,
                topic=final_topic,
                chunk_id=f"existing_{existing_id}",  # Prefix to indicate not newly created
                created_at=None,
            )

        # Format content
        content = self._format_as_markdown(question, answer, final_topic)

        # Generate chunk ID (embedding already created above)
        chunk_id = self._generate_chunk_id(question, answer)

        # Build metadata
        now = datetime.now()
        metadata: dict[str, Any] = {
            "source": "learned_from_llm",
            "category": "Learned Content",
            "original_question": question,
            "topic": final_topic or "general",
            "difficulty": self._estimate_difficulty(question, answer),
            "learned_at": now.isoformat(),
            "verified": True,
        }

        # Add source score info if available
        if source_scores:
            metadata["original_max_score"] = max(source_scores)
            metadata["learning_reason"] = "low_retrieval_confidence"

        # Save to vector store
        await self.vector_store.add(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata],
        )

        return LearnedContent(
            question=question,
            answer=answer,
            topic=final_topic,
            chunk_id=chunk_id,
            created_at=now,
        )

    async def get_learned_count(self) -> int:
        """Get the count of learned chunks in the knowledge base."""
        # This would require a count query - simplified version
        # In practice, you'd query: SELECT COUNT(*) WHERE source = 'learned_from_llm'
        return 0  # Placeholder - implement with actual DB query if needed

    def __repr__(self) -> str:
        return f"KnowledgeLearner(min_answer_length={self.min_answer_length})"
