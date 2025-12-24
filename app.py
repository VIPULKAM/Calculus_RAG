#!/usr/bin/env python3
"""
Calculus RAG - Streamlit Web Interface

A beautiful web interface for the Calculus RAG system with proper LaTeX rendering.

Usage: streamlit run app.py
"""

import asyncio
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.embeddings.ollama_embedder import OllamaEmbedder
from calculus_rag.llm.cloud_llm import CloudLLM
from calculus_rag.llm.model_router import ComplexityLevel, ModelRouter
from calculus_rag.llm.ollama_llm import OllamaLLM
from calculus_rag.rag.pipeline import RAGPipeline
from calculus_rag.retrieval.prerequisite_aware_retriever import PrerequisiteAwareRetriever
from calculus_rag.retrieval.retriever import Retriever
from calculus_rag.vectorstore.pgvector_store import PgVectorStore


# Page configuration
st.set_page_config(
    page_title="Calculus Tutor",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better math rendering
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .math-content {
        font-size: 1.1rem;
        line-height: 1.8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_or_create_eventloop():
    """Get or create an event loop for async operations."""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def fix_latex_rendering(text: str) -> str:
    r"""
    Convert LaTeX delimiters from \[ \] to $$ $$ for Streamlit rendering.

    Also handles inline math delimiters \( \) to $ $.

    Args:
        text: Text containing LaTeX with \[ \] delimiters

    Returns:
        Text with $$ $$ delimiters for Streamlit
    """
    import re

    # Replace display math: [ ... ] -> $$ ... $$
    text = re.sub(r'\\\[', '$$', text)
    text = re.sub(r'\\\]', '$$', text)

    # Also handle bare [ ] that might be used for display math
    # But be careful not to replace actual brackets in text
    text = re.sub(r'(?<!\w)\[(?=\s*\\)', '$$', text)
    text = re.sub(r'(?<=\s)\](?!\w)', '$$', text)

    # Replace inline math: \( ... \) -> $ ... $
    text = re.sub(r'\\\(', '$', text)
    text = re.sub(r'\\\)', '$', text)

    return text


def preprocess_latex_input(text: str) -> str:
    """
    Clean up pasted LaTeX equations from various sources.

    Handles common issues when copying from PDFs, web pages, or LaTeX editors.
    Detects duplicated representations and extracts clean LaTeX.

    Args:
        text: Raw user input that may contain LaTeX

    Returns:
        Cleaned text with proper LaTeX formatting
    """
    import re

    # Remove zero-width characters and other invisible Unicode
    text = re.sub(r'[\u200b\u200c\u200d\ufeff\u00ad]', '', text)

    # If we detect LaTeX commands like \frac, \int, etc., try to extract just the LaTeX part
    # Pattern: duplicated text like "x2−4x2−x−6f(x) = \frac{...} f(x)=x2−x−6x2−4"
    # Keep only the LaTeX version

    # Find LaTeX expressions (text containing backslash commands)
    latex_pattern = r'\\(?:frac|int|sum|sqrt|lim|sin|cos|tan|log|ln)\{[^}]*\}'

    if re.search(latex_pattern, text):
        # Text contains LaTeX - try to clean up duplicates

        # Remove the corrupted non-LaTeX duplicates that appear before/after LaTeX
        # Pattern: variable definitions repeated like "f(x)=..." appearing multiple times
        # Keep the one with LaTeX

        # Remove sequences like "x2−4x2−x−6" (corrupted fractions without proper formatting)
        # These are usually duplicates of the LaTeX version
        text = re.sub(r'([a-z])\(?([a-z])\)?=([a-z0-9])([²³¹0-9])([−\-+])([0-9]+)([a-z0-9])([²³¹0-9])([−\-+])([a-z])([−\-+])([0-9]+)', '', text)

        # Remove trailing corrupted equation copies (after the LaTeX)
        # Pattern like "f(x)=x2−x−6x2−4​" at the end
        text = re.sub(r'\s*[a-z]\([a-z]\)=[a-z0-9−\-+]+​?\s*$', '', text)

        # Remove leading corrupted equation copies (before "Problem:" or the LaTeX)
        text = re.sub(r'^[a-z]\([a-z]\)=[a-z0-9−\-+]+\s*(?=[a-z]\([a-z]\)\s*=\s*\\)', '', text)

    # Fix common Unicode math symbols to LaTeX
    unicode_to_latex = {
        '∫': r'\int ', '∑': r'\sum ', '∏': r'\prod ',
        '√': r'\sqrt', '≤': r'\leq ', '≥': r'\geq ',
        '≠': r'\neq ', '≈': r'\approx ', '∞': r'\infty ',
        '±': r'\pm ', '×': r'\times ', '÷': r'\div ',
        '∂': r'\partial ', '∆': r'\Delta ', 'π': r'\pi ',
        'α': r'\alpha ', 'β': r'\beta ', 'γ': r'\gamma ',
        'θ': r'\theta ', 'λ': r'\lambda ', '→': r'\to ',
        '²': '^2', '³': '^3', '¹': '^1',
        '−': '-',  # Unicode minus to regular minus
    }

    for unicode_char, latex_cmd in unicode_to_latex.items():
        text = text.replace(unicode_char, latex_cmd)

    # Clean up excessive whitespace
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


@st.cache_resource
def initialize_rag_system():
    """Initialize the RAG system (cached to avoid re-initialization)."""
    settings = get_settings()

    # Load embedder
    embedder = OllamaEmbedder(
        model=settings.embedding_model_name,
        base_url=settings.ollama_base_url,
        dimension=settings.vector_dimension,
    )

    # Initialize vector store with new event loop
    async def init_vectorstore():
        vector_store = PgVectorStore(
            connection_string=settings.postgres_dsn,
            dimension=settings.vector_dimension,
            table_name="calculus_knowledge",
        )
        await vector_store.initialize()
        return vector_store

    loop = get_or_create_eventloop()
    vector_store = loop.run_until_complete(init_vectorstore())

    # Initialize Smart Model Router
    small_llm = OllamaLLM(
        model="qwen2-math:1.5b",
        base_url=settings.ollama_base_url,
        timeout=settings.ollama_request_timeout,
    )

    router = ModelRouter(enable_fallback=True)
    router.add_model(
        llm=small_llm,
        name="Fast-1.5B",
        max_complexity=ComplexityLevel.MODERATE,
    )

    # Use cloud LLM for complex queries if enabled (avoids heavy local 7B)
    if settings.cloud_llm_enabled and settings.cloud_llm_api_key:
        if settings.cloud_llm_provider == "ollama-cloud":
            # Ollama cloud models run through local Ollama server
            # Auth is handled via Ollama OAuth (user signs in via browser)
            cloud_llm = OllamaLLM(
                model=settings.cloud_llm_model,  # e.g., "deepseek-v3.1:671b-cloud"
                base_url=settings.ollama_base_url,  # Uses local Ollama
                timeout=settings.cloud_llm_timeout,
                # No API key needed - Ollama uses OAuth session
            )
        else:
            # OpenRouter or DeepSeek direct API
            cloud_llm = CloudLLM(
                api_key=settings.cloud_llm_api_key,
                model=settings.cloud_llm_model,
                provider=settings.cloud_llm_provider,
                timeout=settings.cloud_llm_timeout,
            )
        router.add_model(
            llm=cloud_llm,
            name=f"Cloud-{settings.cloud_llm_model.split('/')[-1].split(':')[0]}",
            max_complexity=ComplexityLevel.COMPLEX,
            is_fallback=True,
        )
    else:
        # Fallback to local 7B if cloud is not configured
        large_llm = OllamaLLM(
            model="qwen2-math:7b",
            base_url=settings.ollama_base_url,
            timeout=600,
        )
        router.add_model(
            llm=large_llm,
            name="Powerful-7B",
            max_complexity=ComplexityLevel.COMPLEX,
            is_fallback=True,
        )

    # Create retrievers
    retriever = Retriever(embedder=embedder, vector_store=vector_store)

    # Create prerequisite-aware retriever with hybrid search for enhanced context
    prereq_retriever = PrerequisiteAwareRetriever(
        embedder=embedder,
        vector_store=vector_store,
        max_prerequisite_depth=2,  # Include prereqs and their prereqs
        prerequisite_weight=0.8,   # Slightly lower weight for prereq content
        use_hybrid_search=True,    # Enable hybrid (semantic + keyword) search
        semantic_weight=0.7,       # 70% semantic, 30% keyword
    )

    # Create RAG pipeline with prerequisite-aware retrieval
    rag_pipeline = RAGPipeline(
        retriever=retriever,
        llm=router,
        n_retrieved_chunks=3,
        prerequisite_aware_retriever=prereq_retriever,
        use_prerequisite_retrieval=True,
    )

    return rag_pipeline, router, vector_store, loop


def query_rag_sync(rag_pipeline, question, temperature, loop):
    """Query the RAG system synchronously (wrapper for async)."""
    async def _query():
        return await rag_pipeline.query(question=question, temperature=temperature)

    return loop.run_until_complete(_query())


def main():
    """Main Streamlit application."""

    # Header
    st.markdown('<div class="main-header">🧮 Calculus Tutor</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="text-align: center; color: #666; margin-bottom: 2rem;">
        Your AI-powered calculus learning assistant with intelligent prerequisite support
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        temperature = st.slider(
            "Response Creativity",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Lower = more focused, Higher = more creative",
        )

        st.divider()

        st.header("📚 Knowledge Base")
        st.info(
            """
            **17 PDFs + 44 Khan Academy Videos:**
            - Paul's Online Notes (Algebra, Calculus)
            - Calculus Cheat Sheets & Practice Problems
            - Khan Academy Video Summaries
            - Study Guides & Reference Materials

            **Total:** 6,835 chunks
            """
        )

        st.divider()

        st.header("🤖 Smart Routing")
        # Show routing info based on configuration
        settings_check = get_settings()
        if settings_check.cloud_llm_enabled and settings_check.cloud_llm_api_key:
            st.success(
                f"""
                **Fast Model:** qwen2-math:1.5b
                - Simple questions
                - Quick responses

                **Cloud Model:** {settings_check.cloud_llm_model}
                - Complex proofs
                - Detailed explanations
                - No local resource usage
                """
            )
        else:
            st.success(
                """
                **Fast Model:** qwen2-math:1.5b
                - Simple questions
                - Quick responses

                **Powerful Model:** qwen2-math:7b
                - Complex proofs
                - Detailed explanations
                """
            )

        st.divider()

        st.header("🔍 Retrieval")
        st.info(
            """
            **Hybrid Search:** Enabled
            - 70% Semantic (meaning)
            - 30% Keyword (BM25)

            **Prerequisite-Aware:** Active
            - Detects topic from query
            - Fetches related foundations
            """
        )

        st.divider()

        st.header("💡 Example Questions")
        examples = [
            "What is a derivative?",
            "Explain the chain rule",
            "Solve x² + 5x + 6 = 0",
            "What is the limit definition?",
            "How do I integrate by parts?",
        ]
        for example in examples:
            if st.button(example, key=f"example_{example}", use_container_width=True):
                st.session_state.example_question = example

        st.divider()

        st.header("📝 Paste Equation")
        with st.expander("Paste messy equation here to clean up"):
            st.markdown("**Paste your equation below, then click Clean & Copy:**")
            messy_input = st.text_area(
                "Paste equation:",
                height=80,
                placeholder="Paste messy LaTeX/equation here...",
                key="messy_equation",
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🧹 Clean & Show", use_container_width=True):
                    if messy_input:
                        cleaned = preprocess_latex_input(messy_input)
                        st.session_state.cleaned_equation = cleaned
            with col2:
                if st.button("📤 Send to Chat", use_container_width=True):
                    if messy_input:
                        cleaned = preprocess_latex_input(messy_input)
                        st.session_state.pending_question = cleaned

            if "cleaned_equation" in st.session_state:
                st.code(st.session_state.cleaned_equation, language=None)

            st.markdown(
                """
                ---
                **Tips for writing equations:**
                - Just type naturally: "What is the integral of x²?"
                - Unicode symbols (∫, ∑, π) are auto-converted
                - Use LaTeX: `\\frac{x}{y}`, `\\int x^2 dx`
                """
            )

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "rag_system" not in st.session_state:
        with st.spinner("🔧 Loading RAG system... (this may take a moment)"):
            (
                st.session_state.rag_system,
                st.session_state.router,
                st.session_state.vector_store,
                st.session_state.event_loop,
            ) = initialize_rag_system()
        st.success("✅ RAG system loaded!")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                # Fix LaTeX rendering and display
                fixed_content = fix_latex_rendering(message["content"])
                st.markdown(fixed_content, unsafe_allow_html=True)
                if "sources" in message:
                    with st.expander("📖 View Sources"):
                        for i, source in enumerate(message["sources"], 1):
                            is_prereq = source.get("is_prerequisite", False)
                            prereq_badge = " 📚 *prerequisite*" if is_prereq else ""
                            st.caption(
                                f"**[{i}]** {source['pdf']} (relevance: {source['score']:.2f}) - {source['category']}{prereq_badge}"
                            )
                # Display model and topic info
                info_parts = []
                if "model" in message:
                    info_parts.append(f"🤖 Model: {message['model']}")
                if message.get("detected_topic"):
                    info_parts.append(f"📍 Topic: {message['detected_topic']}")
                if message.get("prerequisites_used"):
                    info_parts.append(f"📚 Prerequisites: {', '.join(message['prerequisites_used'])}")
                if info_parts:
                    st.caption(" | ".join(info_parts))
            else:
                st.markdown(message["content"])

    # Handle example question clicks
    if "example_question" in st.session_state:
        question = st.session_state.example_question
        del st.session_state.example_question
        st.session_state.messages.append({"role": "user", "content": question})
        st.rerun()

    # Handle pending question from equation cleaner
    if "pending_question" in st.session_state:
        question = st.session_state.pending_question
        del st.session_state.pending_question
        if "cleaned_equation" in st.session_state:
            del st.session_state.cleaned_equation
        st.session_state.messages.append({"role": "user", "content": question})
        st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask a calculus question..."):
        # Preprocess LaTeX input (clean up pasted equations)
        cleaned_prompt = preprocess_latex_input(prompt)

        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": cleaned_prompt})

        with st.chat_message("user"):
            st.markdown(cleaned_prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                # Query RAG system
                response = query_rag_sync(
                    st.session_state.rag_system,
                    cleaned_prompt,
                    temperature,
                    st.session_state.event_loop,
                )

                # Get model used
                model_used = st.session_state.router.last_model_used

                # Fix LaTeX rendering and display answer
                fixed_answer = fix_latex_rendering(response.answer)
                st.markdown(fixed_answer, unsafe_allow_html=True)

                # Display sources with prerequisite info
                if response.sources:
                    with st.expander("📖 View Sources"):
                        for i, source in enumerate(response.sources, 1):
                            pdf_name = source.metadata.get("source", "Unknown")
                            score = source.score
                            category = source.metadata.get("category", "")
                            is_prereq = source.metadata.get("is_prerequisite", False)
                            prereq_badge = " 📚 *prerequisite*" if is_prereq else ""
                            st.caption(
                                f"**[{i}]** {pdf_name} (relevance: {score:.2f}) - {category}{prereq_badge}"
                            )

                # Display topic and prerequisite info
                info_parts = [f"🤖 Model: {model_used}"]
                if response.detected_topic:
                    info_parts.append(f"📍 Topic: {response.detected_topic}")
                if response.prerequisites_used:
                    info_parts.append(f"📚 Prerequisites: {', '.join(response.prerequisites_used)}")
                st.caption(" | ".join(info_parts))

                # Save assistant response
                sources_info = [
                    {
                        "pdf": source.metadata.get("source", "Unknown"),
                        "score": source.score,
                        "category": source.metadata.get("category", ""),
                        "is_prerequisite": source.metadata.get("is_prerequisite", False),
                    }
                    for source in response.sources
                ]
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": response.answer,
                        "sources": sources_info,
                        "model": model_used,
                        "detected_topic": response.detected_topic,
                        "prerequisites_used": response.prerequisites_used,
                    }
                )

    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("📊 Questions asked: " + str(len([m for m in st.session_state.messages if m["role"] == "user"])))
    with col2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col3:
        st.caption("💡 Powered by Qwen2-Math + Hybrid Search (pgvector + BM25)")


if __name__ == "__main__":
    main()
