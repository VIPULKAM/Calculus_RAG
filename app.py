#!/usr/bin/env python3
"""
Calculus RAG - Streamlit Web Interface

A beautiful web interface for the Calculus RAG system with proper LaTeX rendering.

Usage: streamlit run app.py
"""

import asyncio
import sys
import threading
from pathlib import Path

import requests

# Disable uvloop before importing other modules to allow nest_asyncio
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

import nest_asyncio
import streamlit as st

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

sys.path.insert(0, str(Path(__file__).parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.embeddings.ollama_embedder import OllamaEmbedder
from calculus_rag.learning import KnowledgeLearner
from calculus_rag.llm.cloud_llm import CloudLLM
from calculus_rag.llm.model_router import ComplexityLevel, ModelRouter, QueryDomain
from calculus_rag.llm.ollama_llm import OllamaLLM
from calculus_rag.rag.pipeline import RAGPipeline
from calculus_rag.retrieval.prerequisite_aware_retriever import PrerequisiteAwareRetriever
from calculus_rag.retrieval.retriever import Retriever
from calculus_rag.vectorstore.pgvector_store import PgVectorStore


def get_available_cloud_models() -> list[str]:
    """Fetch available cloud models from Ollama."""
    settings = get_settings()
    try:
        response = requests.get(
            f"{settings.ollama_base_url}/api/tags",
            timeout=5
        )
        if response.status_code == 200:
            models = response.json().get("models", [])
            # Filter for cloud models (have -cloud suffix or :cloud tag)
            cloud_models = [
                m["name"] for m in models
                if "-cloud" in m["name"] or ":cloud" in m["name"]
            ]
            return sorted(cloud_models)
    except Exception:
        pass
    return []


def create_llm_for_model(model_name: str):
    """Create an OllamaLLM instance for a specific model."""
    settings = get_settings()
    return OllamaLLM(
        model=model_name,
        base_url=settings.ollama_base_url,
        timeout=settings.cloud_llm_timeout,
    )


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
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Loop is closed")
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_knowledge_base_stats():
    """Get dynamic stats from the database."""
    import asyncpg

    async def fetch_stats():
        settings = get_settings()
        try:
            conn = await asyncpg.connect(settings.postgres_dsn)

            # Total chunks
            total = await conn.fetchval("SELECT COUNT(*) FROM calculus_knowledge")

            # Count by source type
            sources = await conn.fetch("""
                SELECT
                    CASE
                        WHEN metadata->>'source' LIKE '%.pdf' THEN 'pdf'
                        WHEN metadata->>'source' LIKE '%.md' THEN 'markdown'
                        ELSE 'other'
                    END as source_type,
                    COUNT(*) as count
                FROM calculus_knowledge
                GROUP BY source_type
            """)

            # Count unique sources
            unique_sources = await conn.fetchval("""
                SELECT COUNT(DISTINCT metadata->>'source') FROM calculus_knowledge
            """)

            await conn.close()

            pdf_count = 0
            md_count = 0
            for row in sources:
                if row['source_type'] == 'pdf':
                    pdf_count = row['count']
                elif row['source_type'] == 'markdown':
                    md_count = row['count']

            return {
                'total': total or 0,
                'pdf_chunks': pdf_count,
                'markdown_chunks': md_count,
                'unique_sources': unique_sources or 0,
            }
        except Exception:
            # Return defaults if DB not available
            return {
                'total': 0,
                'pdf_chunks': 0,
                'markdown_chunks': 0,
                'unique_sources': 0,
            }

    loop = get_or_create_eventloop()
    return loop.run_until_complete(fetch_stats())


def fix_latex_rendering(text: str) -> str:
    r"""
    Convert various LaTeX formats to Streamlit-compatible $$ $$ and $ $ delimiters.

    Handles multiple LaTeX delimiter styles from different LLMs:
    - \[ \] -> $$ $$
    - \( \) -> $ $
    - \begin{equation} \end{equation} -> $$ $$
    - \begin{align} \end{align} -> $$ $$
    - <think>...</think> tags (DeepSeek R1) -> removed
    - Double backslashes -> single backslashes

    Args:
        text: Text containing LaTeX with various delimiters

    Returns:
        Text with Streamlit-compatible delimiters
    """
    import re

    # Remove DeepSeek R1 thinking tags (keep content between them hidden)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

    # Fix double-escaped backslashes (\\frac -> \frac) common in JSON
    # But be careful: $$ should stay as $$, not become $
    text = re.sub(r'\\\\(?=[a-zA-Z])', r'\\', text)

    # Replace display math: \[ ... \] -> $$ ... $$
    text = re.sub(r'\\\[', '$$', text)
    text = re.sub(r'\\\]', '$$', text)

    # Replace inline math: \( ... \) -> $ ... $
    text = re.sub(r'\\\(', '$', text)
    text = re.sub(r'\\\)', '$', text)

    # Replace \begin{equation} ... \end{equation} -> $$ ... $$
    text = re.sub(r'\\begin\{equation\*?\}', '$$', text)
    text = re.sub(r'\\end\{equation\*?\}', '$$', text)

    # Replace \begin{align} ... \end{align} -> $$ ... $$
    text = re.sub(r'\\begin\{align\*?\}', '$$', text)
    text = re.sub(r'\\end\{align\*?\}', '$$', text)

    # Replace \begin{gather} ... \end{gather} -> $$ ... $$
    text = re.sub(r'\\begin\{gather\*?\}', '$$', text)
    text = re.sub(r'\\end\{gather\*?\}', '$$', text)

    # Handle bare [ ] that might be used for display math
    # But be careful not to replace actual brackets in text
    text = re.sub(r'(?<!\w)\[(?=\s*\\)', '$$', text)
    text = re.sub(r'(?<=\s)\](?!\w)', '$$', text)

    # Clean up any triple or quadruple $$ that might result from conversions
    text = re.sub(r'\${4,}', '$$', text)
    text = re.sub(r'\${3}', '$$', text)

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

    # Initialize vector store
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

    # Initialize Smart Model Router with Domain-Aware Routing
    # Math models (local, fast)
    small_llm = OllamaLLM(
        model="qwen2-math:1.5b",
        base_url=settings.ollama_base_url,
        timeout=settings.ollama_request_timeout,
    )

    router = ModelRouter(enable_fallback=True)
    router.add_model(
        llm=small_llm,
        name="Fast-Math-1.5B",
        max_complexity=ComplexityLevel.MODERATE,
        domains=[QueryDomain.MATH],  # Math-specific model
    )

    # Use cloud LLMs for specialized routing
    # For ollama-cloud provider, API key is not needed (uses OAuth)
    cloud_enabled = settings.cloud_llm_enabled and (
        settings.cloud_llm_api_key or settings.cloud_llm_provider == "ollama-cloud"
    )
    if cloud_enabled:
        # Code-specialized model (devstral for code questions)
        code_llm = OllamaLLM(
            model="devstral-2:123b-cloud",
            base_url=settings.ollama_base_url,
            timeout=settings.cloud_llm_timeout,
        )
        router.add_model(
            llm=code_llm,
            name="Code-Devstral",
            max_complexity=ComplexityLevel.COMPLEX,
            domains=[QueryDomain.CODE],  # Code-specific model
        )

        # Heavy reasoning model for math proofs and complex queries
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
            domains=[QueryDomain.MATH, QueryDomain.GENERAL],  # Math + general fallback
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
            domains=[QueryDomain.MATH, QueryDomain.GENERAL, QueryDomain.CODE],
            is_fallback=True,
        )

    # Create retrievers with reranking for better relevance
    retriever = Retriever(
        embedder=embedder,
        vector_store=vector_store,
        use_reranking=True,        # Enable BGE reranker for better relevance
        rerank_candidates=20,      # Fetch 20 candidates, rerank to top 5
    )

    # Create prerequisite-aware retriever with hybrid search and reranking
    prereq_retriever = PrerequisiteAwareRetriever(
        embedder=embedder,
        vector_store=vector_store,
        max_prerequisite_depth=2,  # Include prereqs and their prereqs
        prerequisite_weight=0.8,   # Slightly lower weight for prereq content
        use_hybrid_search=True,    # Enable hybrid (semantic + keyword) search
        semantic_weight=0.5,       # 50% semantic, 50% keyword (balanced for math terms)
        use_reranking=True,        # Enable BGE reranker for better relevance
        rerank_candidates=20,      # Fetch 20 candidates, rerank to top results
    )

    # Create RAG pipeline with prerequisite-aware retrieval
    rag_pipeline = RAGPipeline(
        retriever=retriever,
        llm=router,
        n_retrieved_chunks=3,
        prerequisite_aware_retriever=prereq_retriever,
        use_prerequisite_retrieval=True,
    )

    # Create knowledge learner for self-improvement
    learner = KnowledgeLearner(
        embedder=embedder,
        vector_store=vector_store,
        min_answer_length=50,
    )

    return rag_pipeline, router, vector_store, loop, learner


# Lock to serialize async operations and prevent concurrent run_until_complete calls
_async_lock = threading.Lock()


def query_rag_sync(rag_pipeline, question, temperature, loop, conversation_history=None, llm_override=None):
    """Query the RAG system synchronously (wrapper for async)."""
    async def _query():
        return await rag_pipeline.query(
            question=question,
            temperature=temperature,
            conversation_history=conversation_history,
            llm_override=llm_override,
        )

    with _async_lock:
        return loop.run_until_complete(_query())


def save_to_knowledge_base(learner, question, answer, detected_topic, source_scores, loop):
    """Save a verified answer to the knowledge base."""
    async def _save():
        return await learner.learn(
            question=question,
            answer=answer,
            detected_topic=detected_topic,
            source_scores=source_scores,
        )

    with _async_lock:
        return loop.run_until_complete(_save())


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

        # Model selector
        cloud_models = get_available_cloud_models()
        model_options = ["Auto (Smart Routing)"] + cloud_models

        selected_model = st.selectbox(
            "🤖 Model Selection",
            options=model_options,
            index=0,
            help="Auto uses smart routing based on question complexity. Or select a specific cloud model.",
        )

        # Store selection in session state
        if selected_model == "Auto (Smart Routing)":
            st.session_state.selected_model = None
        else:
            st.session_state.selected_model = selected_model

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
        # Get dynamic stats from database
        stats = get_knowledge_base_stats()
        if stats['total'] > 0:
            st.info(
                f"""
                **{stats['unique_sources']} Sources Loaded:**
                - Paul's Online Notes (Algebra, Calculus)
                - Calculus Cheat Sheets & Practice Problems
                - Khan Academy Video Summaries
                - Study Guides & Reference Materials

                **Total:** {stats['total']:,} chunks
                """
            )
        else:
            st.warning("⚠️ Knowledge base not loaded. Run ingestion first.")

        st.divider()

        st.header("🤖 Smart Routing")
        # Show routing info based on configuration and selection
        settings_check = get_settings()
        cloud_enabled = settings_check.cloud_llm_enabled and (
            settings_check.cloud_llm_api_key or settings_check.cloud_llm_provider == "ollama-cloud"
        )

        if st.session_state.get("selected_model"):
            # Manual model selection
            st.info(
                f"""
                **Selected Model:** {st.session_state.selected_model}

                ⚠️ Auto-routing disabled
                Using selected cloud model for all questions.
                """
            )
        elif cloud_enabled:
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

        st.header("💬 Conversation")
        msg_count = len(st.session_state.get("messages", []))
        if msg_count > 0:
            st.success(f"**Memory Active:** {msg_count} messages\n\nI remember our conversation!")
        else:
            st.info("Start chatting - I'll remember context!")

        st.divider()

        st.header("💡 Example Questions")
        st.caption("Click any question to try it:")

        # Organized by difficulty/topic
        example_categories = {
            "📗 Basics": [
                "What is a derivative?",
                "Explain limits with an example",
            ],
            "📘 How-To": [
                "How do I use the chain rule?",
                "How do I integrate by parts?",
            ],
            "📙 Problem Solving": [
                "Find the derivative of sin(x²)",
                "Evaluate the limit of (x²-1)/(x-1) as x→1",
            ],
            "📕 Conceptual": [
                "Why does the derivative of eˣ equal eˣ?",
                "What's the relationship between derivatives and integrals?",
            ],
        }

        for category, questions in example_categories.items():
            st.markdown(f"**{category}**")
            for q in questions:
                if st.button(q, key=f"ex_{hash(q)}", use_container_width=True):
                    st.session_state.example_question = q

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
    if "pending_save" not in st.session_state:
        st.session_state.pending_save = None

    # Process any pending save action (from button click)
    if st.session_state.pending_save is not None:
        save_data = st.session_state.pending_save
        st.session_state.pending_save = None
        try:
            # Need to reinitialize learner if not in session state
            if "learner" in st.session_state:
                result = save_to_knowledge_base(
                    st.session_state.learner,
                    save_data["question"],
                    save_data["answer"],
                    save_data["topic"],
                    save_data["scores"],
                    st.session_state.event_loop,
                )
                # Update message state
                if save_data["msg_idx"] < len(st.session_state.messages):
                    st.session_state.messages[save_data["msg_idx"]]["saved_to_kb"] = True

                # Check if it was a duplicate (chunk_id starts with "existing_")
                if result.chunk_id and result.chunk_id.startswith("existing_"):
                    st.info(f"ℹ️ Similar content already exists in knowledge base (ID: {result.chunk_id[9:]})")
                else:
                    st.success(f"✅ Saved to knowledge base! (ID: {result.chunk_id})")
        except Exception as e:
            st.error(f"Failed to save: {e}")

    if "rag_system" not in st.session_state:
        with st.spinner("🔧 Loading RAG system... (this may take a moment)"):
            (
                st.session_state.rag_system,
                st.session_state.router,
                st.session_state.vector_store,
                st.session_state.event_loop,
                st.session_state.learner,
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

                # Learning feature: Feedback buttons for low-confidence responses
                if message.get("low_confidence") and not message.get("saved_to_kb"):
                    msg_idx = st.session_state.messages.index(message)
                    col1, col2, col3 = st.columns([1, 1, 4])
                    with col1:
                        if st.button("👍 Save to KB", key=f"save_{msg_idx}", help="Save this answer to improve future responses"):
                            st.session_state.pending_save = {
                                "question": message.get("original_question", ""),
                                "answer": message["content"],
                                "topic": message.get("detected_topic"),
                                "scores": message.get("source_scores", []),
                                "msg_idx": msg_idx,
                            }
                            st.rerun()
                    with col2:
                        if st.button("👎 Dismiss", key=f"dismiss_{msg_idx}", help="Don't save this answer"):
                            st.session_state.messages[msg_idx]["low_confidence"] = False
                            st.rerun()
                elif message.get("saved_to_kb"):
                    st.success("✅ Saved to knowledge base")
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
                # Build conversation history (exclude current message)
                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]  # All except current
                ]

                # Check if a specific model is selected (override auto routing)
                llm_override = None
                if st.session_state.get("selected_model"):
                    llm_override = create_llm_for_model(st.session_state.selected_model)

                # Query RAG system with conversation context
                response = query_rag_sync(
                    st.session_state.rag_system,
                    cleaned_prompt,
                    temperature,
                    st.session_state.event_loop,
                    conversation_history=history if history else None,
                    llm_override=llm_override,
                )

                # Get model used
                if st.session_state.get("selected_model"):
                    model_used = st.session_state.selected_model
                else:
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

                # Save assistant response with learning metadata FIRST (before buttons)
                sources_info = [
                    {
                        "pdf": source.metadata.get("source", "Unknown"),
                        "score": source.score,
                        "category": source.metadata.get("category", ""),
                        "is_prerequisite": source.metadata.get("is_prerequisite", False),
                    }
                    for source in response.sources
                ]

                # Generate unique message ID for feedback tracking
                msg_id = len(st.session_state.messages)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": response.answer,
                        "sources": sources_info,
                        "model": model_used,
                        "detected_topic": response.detected_topic,
                        "prerequisites_used": response.prerequisites_used,
                        "low_confidence": response.low_confidence,
                        "source_scores": response.source_scores,
                        "original_question": cleaned_prompt,
                        "msg_id": msg_id,
                        "saved_to_kb": False,
                    }
                )

                # Learning feature: Show feedback buttons for low-confidence responses
                if response.low_confidence:
                    st.info("💡 **Low retrieval confidence** - If this answer is helpful, you can save it to improve future responses.")
                    col1, col2, col3 = st.columns([1, 1, 4])
                    with col1:
                        if st.button("👍 Save to KB", key=f"save_new_{msg_id}", help="Save this answer to improve future responses"):
                            st.session_state.pending_save = {
                                "question": cleaned_prompt,
                                "answer": response.answer,
                                "topic": response.detected_topic,
                                "scores": response.source_scores,
                                "msg_idx": msg_id,
                            }
                            st.rerun()
                    with col2:
                        if st.button("👎 Dismiss", key=f"dismiss_new_{msg_id}", help="Don't save this answer"):
                            st.session_state.messages[msg_id]["low_confidence"] = False
                            st.rerun()

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
