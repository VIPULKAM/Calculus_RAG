"""
RAG (Retrieval-Augmented Generation) pipeline.

Orchestrates retrieval, prerequisite detection, and LLM generation to answer
calculus questions with adaptive support.
"""

from dataclasses import dataclass

from calculus_rag.llm.base import BaseLLM, LLMMessage
from calculus_rag.retrieval.retriever import Retriever, RetrievalResult
from calculus_rag.retrieval.prerequisite_aware_retriever import (
    PrerequisiteAwareRetriever,
    PrerequisiteAwareResult,
)


@dataclass
class RAGResponse:
    """
    Represents a response from the RAG system.

    Attributes:
        answer: The generated answer to the user's question.
        sources: List of retrieved document chunks used to generate the answer.
        prerequisites_detected: Topics the user may need to learn first.
        detected_topic: The main topic detected from the query.
        prerequisites_used: Prerequisite topics that were searched.
        confidence: Optional confidence score for the answer.
    """

    answer: str
    sources: list[RetrievalResult]
    prerequisites_detected: list[str] | None = None
    detected_topic: str | None = None
    prerequisites_used: list[str] | None = None
    confidence: float | None = None


class RAGPipeline:
    """
    RAG pipeline for calculus question answering.

    The pipeline:
    1. Retrieves relevant content chunks using semantic search
    2. Detects missing prerequisites (optional)
    3. Generates a contextualized answer using the LLM
    4. Returns structured response with sources

    Example:
        >>> pipeline = RAGPipeline(retriever=retriever, llm=llm)
        >>> response = await pipeline.query("What is a derivative?")
        >>> print(response.answer)
        >>> for source in response.sources:
        ...     print(f"Source: {source.metadata['topic']}")
    """

    def __init__(
        self,
        retriever: Retriever,
        llm: BaseLLM,
        system_prompt: str | None = None,
        n_retrieved_chunks: int = 5,
        prerequisite_aware_retriever: PrerequisiteAwareRetriever | None = None,
        use_prerequisite_retrieval: bool = True,
    ) -> None:
        """
        Initialize the RAG pipeline.

        Args:
            retriever: The retriever for semantic search.
            llm: The language model for generating answers.
            system_prompt: Optional system prompt to guide the LLM.
            n_retrieved_chunks: Number of chunks to retrieve per query.
            prerequisite_aware_retriever: Optional prerequisite-aware retriever.
            use_prerequisite_retrieval: Whether to use prerequisite-aware retrieval.
        """
        self.retriever = retriever
        self.llm = llm
        self.n_retrieved_chunks = n_retrieved_chunks
        self.prerequisite_retriever = prerequisite_aware_retriever
        self.use_prerequisite_retrieval = use_prerequisite_retrieval

        # Default system prompt for calculus tutoring
        self.system_prompt = system_prompt or self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        """Return the default system prompt for calculus tutoring."""
        return """You are an expert calculus tutor helping high school students.

Your role:
- Provide clear, step-by-step explanations
- Use simple language while being mathematically precise
- Build on students' existing knowledge
- Identify when prerequisite concepts are needed
- Use relevant examples and visualizations when helpful

When answering:
1. ONLY answer the student's specific question - ignore any other problems or examples in the context
2. Use the provided context from the knowledge base as reference material
3. If prerequisite knowledge is needed, mention it
4. Keep answers focused and concise
5. Use LaTeX notation for math (e.g., $f(x)$, $$\\lim_{x \\to a}$$)

IMPORTANT: The context may contain multiple problems or examples. You must ONLY address the student's question, not other problems that appear in the context.

Remember: Your goal is to help students understand, not just provide answers."""

    async def query(
        self,
        question: str,
        filters: dict | None = None,
        temperature: float = 0.7,
        detect_prerequisites: bool = False,
        conversation_history: list[dict] | None = None,
    ) -> RAGResponse:
        """
        Answer a question using retrieval-augmented generation.

        Args:
            question: The user's question about calculus.
            filters: Optional filters for retrieval (e.g., {"topic": "limits"}).
            temperature: LLM temperature for generation (0-1).
            detect_prerequisites: Whether to detect missing prerequisites.
            conversation_history: Optional list of previous messages for context.
                Each message should have 'role' ('user' or 'assistant') and 'content'.

        Returns:
            RAGResponse: The answer with sources and metadata.

        Raises:
            ValueError: If question is empty.
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        detected_topic = None
        prerequisites_used = None

        # Step 1: Retrieve relevant chunks
        # Use prerequisite-aware retrieval if available and enabled
        if self.prerequisite_retriever and self.use_prerequisite_retrieval:
            prereq_result = await self.prerequisite_retriever.retrieve(
                query=question,
                n_results=self.n_retrieved_chunks,
                n_prerequisite_results=2,  # 2 results per prerequisite topic
                filters=filters,
            )
            sources = prereq_result.results[:self.n_retrieved_chunks + 4]  # Allow extra prereq content
            detected_topic = prereq_result.detected_topic
            prerequisites_used = prereq_result.prerequisites_used
        else:
            # Fallback to standard retrieval
            sources = await self.retriever.retrieve(
                query=question,
                n_results=self.n_retrieved_chunks,
                filters=filters,
            )

        # Step 2: Build context from retrieved chunks
        context = self._build_context(sources)

        # Step 3: Generate answer using LLM
        messages = [
            LLMMessage(role="system", content=self.system_prompt),
        ]

        # Add conversation history for context (last N exchanges)
        if conversation_history:
            for msg in conversation_history[-10:]:  # Keep last 5 Q&A pairs (10 messages)
                messages.append(LLMMessage(role=msg["role"], content=msg["content"]))

        # Add current question with context
        messages.append(
            LLMMessage(
                role="user",
                content=self._build_user_prompt(question, context),
            ),
        )

        llm_response = self.llm.generate(messages, temperature=temperature)
        answer = llm_response.content

        # Step 4: Detect prerequisites (optional)
        prerequisites = None
        if detect_prerequisites:
            prerequisites = await self._detect_prerequisites(question, sources)

        return RAGResponse(
            answer=answer,
            sources=sources,
            prerequisites_detected=prerequisites,
            detected_topic=detected_topic,
            prerequisites_used=prerequisites_used,
        )

    async def query_stream(
        self,
        question: str,
        filters: dict | None = None,
        temperature: float = 0.7,
    ):
        """
        Stream answer generation for a question.

        Args:
            question: The user's question about calculus.
            filters: Optional filters for retrieval.
            temperature: LLM temperature for generation (0-1).

        Yields:
            str: Chunks of the generated answer.

        Raises:
            ValueError: If question is empty.
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        # Retrieve relevant chunks
        sources = await self.retriever.retrieve(
            query=question,
            n_results=self.n_retrieved_chunks,
            filters=filters,
        )

        # Build context and messages
        context = self._build_context(sources)
        messages = [
            LLMMessage(role="system", content=self.system_prompt),
            LLMMessage(
                role="user",
                content=self._build_user_prompt(question, context),
            ),
        ]

        # Stream response from LLM
        for chunk in self.llm.generate_stream(messages, temperature=temperature):
            yield chunk

    def _build_context(self, sources: list[RetrievalResult]) -> str:
        """
        Build context string from retrieved sources.

        Args:
            sources: Retrieved document chunks.

        Returns:
            str: Formatted context for the LLM.
        """
        if not sources:
            return "No relevant content found in the knowledge base."

        context_parts = []
        for i, source in enumerate(sources, 1):
            topic = source.metadata.get("topic", "Unknown")
            difficulty = source.metadata.get("difficulty", "?")
            is_prereq = source.metadata.get("is_prerequisite", False)

            # Mark prerequisite content clearly
            source_type = "Prerequisite" if is_prereq else "Main"
            context_parts.append(
                f"[Source {i} - {source_type} - Topic: {topic}, Difficulty: {difficulty}]\n"
                f"{source.content}\n"
            )

        return "\n".join(context_parts)

    def _build_user_prompt(self, question: str, context: str) -> str:
        """
        Build the user prompt with question and context.

        Args:
            question: The user's question.
            context: Retrieved context from knowledge base.

        Returns:
            str: Formatted prompt for the LLM.
        """
        return f"""Context from knowledge base:
{context}

Student Question: {question}

Please provide a clear, helpful answer based on the context above. If the context doesn't contain enough information, acknowledge this and provide what guidance you can."""

    async def _detect_prerequisites(
        self,
        question: str,
        sources: list[RetrievalResult],
    ) -> list[str]:
        """
        Detect missing prerequisites for the question.

        Args:
            question: The user's question.
            sources: Retrieved sources.

        Returns:
            list[str]: List of prerequisite topic identifiers.

        Note:
            This is a placeholder. Full prerequisite detection will use
            the prerequisite graph and detector.
        """
        # TODO: Implement full prerequisite detection
        # For now, extract unique topics from sources as potential prerequisites
        topics = set()
        for source in sources:
            if "topic" in source.metadata:
                topics.add(source.metadata["topic"])

        return sorted(topics)

    def __repr__(self) -> str:
        return (
            f"RAGPipeline(llm={self.llm.model_name}, "
            f"n_chunks={self.n_retrieved_chunks})"
        )
