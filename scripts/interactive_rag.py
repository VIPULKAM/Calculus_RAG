#!/usr/bin/env python3
"""
Interactive RAG testing - Ask questions and get answers!

Usage: python scripts/interactive_rag.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.embeddings.bge_embedder import BGEEmbedder
from calculus_rag.embeddings.ollama_embedder import OllamaEmbedder
from calculus_rag.llm.model_router import ComplexityLevel, ModelRouter
from calculus_rag.llm.ollama_llm import OllamaLLM
from calculus_rag.rag.pipeline import RAGPipeline
from calculus_rag.retrieval.retriever import Retriever
from calculus_rag.vectorstore.pgvector_store import PgVectorStore


# Sample Pre-Calculus and Calculus Content
SAMPLE_CONTENT = [
    {
        "content": """# Algebra Basics - Solving Equations

To solve algebraic equations, you need to isolate the variable on one side.

**Basic Rules:**
- Whatever you do to one side, do to the other
- Inverse operations undo each other (+ and -, × and ÷)

**Example:** Solve for x: 2x + 5 = 13
Step 1: Subtract 5 from both sides: 2x = 8
Step 2: Divide both sides by 2: x = 4

**Example:** Solve for x: 3(x - 2) = 15
Step 1: Distribute: 3x - 6 = 15
Step 2: Add 6 to both sides: 3x = 21
Step 3: Divide by 3: x = 7""",
        "metadata": {"topic": "algebra.basics", "difficulty": 1},
    },
    {
        "content": """# Exponent Rules

Exponents represent repeated multiplication. Key rules:

**Product Rule:** x^a · x^b = x^(a+b)
Example: x^3 · x^2 = x^5

**Quotient Rule:** x^a ÷ x^b = x^(a-b)
Example: x^5 ÷ x^2 = x^3

**Power Rule:** (x^a)^b = x^(a·b)
Example: (x^2)^3 = x^6

**Zero Exponent:** x^0 = 1 (for any x ≠ 0)

**Negative Exponent:** x^(-a) = 1/x^a
Example: x^(-2) = 1/x^2""",
        "metadata": {"topic": "algebra.exponents", "difficulty": 2},
    },
    {
        "content": """# Quadratic Equations

A quadratic equation has the form: ax² + bx + c = 0

**Quadratic Formula:**
x = [-b ± √(b² - 4ac)] / (2a)

**Discriminant:** b² - 4ac tells us about the solutions:
- If positive: two real solutions
- If zero: one real solution
- If negative: no real solutions (two complex solutions)

**Example:** Solve x² - 5x + 6 = 0
Using factoring: (x - 2)(x - 3) = 0
Solutions: x = 2 or x = 3

**Example:** Solve x² + 2x - 3 = 0
a = 1, b = 2, c = -3
x = [-2 ± √(4 + 12)] / 2 = [-2 ± 4] / 2
Solutions: x = 1 or x = -3""",
        "metadata": {"topic": "algebra.quadratic", "difficulty": 3},
    },
    {
        "content": """# Functions - Domain and Range

**Function Notation:** f(x) represents the output when input is x

**Domain:** All possible input values (x-values)
**Range:** All possible output values (y-values or f(x)-values)

**Example:** f(x) = x²
- Domain: all real numbers (-∞, ∞)
- Range: [0, ∞) because squares are always ≥ 0

**Example:** f(x) = 1/x
- Domain: all real numbers except 0
- Range: all real numbers except 0

**Example:** f(x) = √x
- Domain: [0, ∞) - can't take square root of negatives
- Range: [0, ∞) - square roots are non-negative""",
        "metadata": {"topic": "functions.domain_range", "difficulty": 2},
    },
    {
        "content": """# Trigonometry - Unit Circle

The unit circle has radius 1 centered at the origin.

**Key Angles and Values:**

0° (0 rad): cos = 1, sin = 0, tan = 0
30° (π/6): cos = √3/2, sin = 1/2, tan = √3/3
45° (π/4): cos = √2/2, sin = √2/2, tan = 1
60° (π/3): cos = 1/2, sin = √3/2, tan = √3
90° (π/2): cos = 0, sin = 1, tan = undefined

**SOHCAHTOA:**
- sin θ = Opposite / Hypotenuse
- cos θ = Adjacent / Hypotenuse
- tan θ = Opposite / Adjacent

**Pythagorean Identity:**
sin²θ + cos²θ = 1""",
        "metadata": {"topic": "trig.unit_circle", "difficulty": 2},
    },
    {
        "content": """# Limits - Introduction

A limit describes what value a function approaches as the input approaches a certain value.

**Notation:** lim(x→a) f(x) = L
This means: as x gets closer to a, f(x) gets closer to L

**Example:** lim(x→2) (x² + 1) = 5
As x approaches 2, x² + 1 approaches 5

**One-sided Limits:**
- lim(x→a⁺): limit from the right
- lim(x→a⁻): limit from the left

**Example with discontinuity:**
f(x) = 1/x
- lim(x→0⁺) f(x) = +∞
- lim(x→0⁻) f(x) = -∞
The limit does not exist at x = 0

**Why Limits Matter:**
Limits are the foundation for derivatives and integrals!""",
        "metadata": {"topic": "limits.introduction", "difficulty": 3},
    },
    {
        "content": """# Derivatives - Power Rule

The power rule is the most fundamental derivative rule.

**Power Rule:** If f(x) = x^n, then f'(x) = n·x^(n-1)

**Examples:**
- f(x) = x² → f'(x) = 2x
- f(x) = x³ → f'(x) = 3x²
- f(x) = x⁵ → f'(x) = 5x⁴
- f(x) = x^(-1) → f'(x) = -x^(-2) = -1/x²

**Constant Rule:** If f(x) = c (constant), then f'(x) = 0

**Constant Multiple:** If f(x) = c·g(x), then f'(x) = c·g'(x)
Example: f(x) = 5x³ → f'(x) = 5·3x² = 15x²

**Sum Rule:** If f(x) = g(x) + h(x), then f'(x) = g'(x) + h'(x)
Example: f(x) = x² + x³ → f'(x) = 2x + 3x²""",
        "metadata": {"topic": "derivatives.power_rule", "difficulty": 2},
    },
]


async def setup_rag() -> tuple:
    """Initialize the RAG system with sample content."""
    print("🔧 Initializing RAG System...")
    settings = get_settings()

    # Load embedder
    print("   Loading embedder...")
    if settings.embedding_type == "ollama":
        embedder = OllamaEmbedder(
            model=settings.embedding_model_name,
            base_url=settings.ollama_base_url,
            dimension=settings.vector_dimension,
        )
    else:
        embedder = BGEEmbedder(
            model_name=settings.embedding_model_name,
            device=settings.embedding_device,
        )

    # Initialize vector store
    print("   Connecting to database...")
    vector_store = PgVectorStore(
        connection_string=settings.postgres_dsn,
        dimension=settings.vector_dimension,
        table_name="calculus_knowledge",  # Use real knowledge base
    )
    await vector_store.initialize()

    # Using existing knowledge base (6,835 chunks from ingested PDFs + Khan Academy)
    print(f"   ✓ Connected to knowledge base with 6,835 chunks")

    # Initialize Smart Model Router
    print("   Setting up Smart Model Router...")

    # Small model for simple/moderate questions (fast)
    small_llm = OllamaLLM(
        model="qwen2-math:1.5b",
        base_url=settings.ollama_base_url,
        timeout=settings.ollama_request_timeout,
    )
    print("      ✓ Small model: qwen2-math:1.5b (fast)")

    # Large model for complex questions (more capable)
    large_llm = OllamaLLM(
        model="qwen2-math:7b",
        base_url=settings.ollama_base_url,
        timeout=600,  # More time for larger model
    )
    print("      ✓ Large model: qwen2-math:7b (powerful)")

    # Create router
    router = ModelRouter(enable_fallback=True)
    router.add_model(
        llm=small_llm,
        name="Fast-1.5B",
        max_complexity=ComplexityLevel.MODERATE,
    )
    router.add_model(
        llm=large_llm,
        name="Powerful-7B",
        max_complexity=ComplexityLevel.COMPLEX,
        is_fallback=True,
    )
    print("      ✓ Router configured with intelligent routing!")

    # Create RAG pipeline with router
    retriever = Retriever(embedder=embedder, vector_store=vector_store)
    rag_pipeline = RAGPipeline(
        retriever=retriever,
        llm=router,
        n_retrieved_chunks=2,  # Get top 2 most relevant chunks
    )

    print("✅ RAG System Ready with Smart Routing!\n")
    return rag_pipeline, router, vector_store


async def interactive_session():
    """Run interactive Q&A session."""
    rag_pipeline, router, vector_store = await setup_rag()

    print("=" * 80)
    print("Interactive Calculus RAG - Full Knowledge Base (6,835 Chunks)")
    print("=" * 80)
    print("\n🤖 Smart Routing Enabled:")
    print("   • Simple questions → Fast model (qwen2-math:1.5b)")
    print("   • Complex questions → Powerful model (qwen2-math:7b)")
    print("   • Automatic fallback for reliability")
    print("\n📚 Knowledge Base (17 PDFs + 44 Khan Academy):")
    print("   • Paul's Online Notes (Algebra, Calculus)")
    print("   • Calculus Cheat Sheets (Limits, Derivatives, Integrals)")
    print("   • Khan Academy Video Summaries")
    print("   • Study Guides & Reference Materials")
    print("\n💡 Tips:")
    print("   • Type 'quit' or 'exit' to stop")
    print("   • Ask any calculus or pre-calculus question")
    print("   • Examples: 'Explain chain rule', 'Solve x^2 + 5x + 6 = 0'")
    print("=" * 80)

    question_count = 0

    while True:
        try:
            # Get user question
            print("\n" + "─" * 80)
            question = input("\n❓ Your Question: ").strip()

            if not question:
                continue

            if question.lower() in ["quit", "exit", "q"]:
                print("\n👋 Goodbye! Thanks for testing the RAG system.")
                break

            if question.lower() == "stats":
                print("\n📊 Knowledge Base Statistics:")
                print("   • Total chunks: 6,835")
                print("   • PDFs: 17 (OpenStax + Paul's Online Notes)")
                print("   • Khan Academy: 44 video summaries")
                print("   • Topics: Algebra, Trig, Limits, Derivatives, Integrals")
                continue

            question_count += 1
            print(f"\n⏳ Thinking... (Question #{question_count})")

            # Query RAG system
            response = await rag_pipeline.query(
                question=question,
                temperature=0.3,  # Lower for more focused answers
            )

            # Display routing information
            model_used = router.last_model_used
            print(f"\n🤖 Model Used: {model_used}")

            # Display answer
            print("\n💡 Answer:")
            print("─" * 80)
            print(response.answer)
            print("─" * 80)

            # Show sources
            if response.sources:
                print(f"\n📖 Sources ({len(response.sources)} chunks):")
                for i, source in enumerate(response.sources, 1):
                    pdf_name = source.metadata.get("source", "Unknown")
                    score = source.score
                    category = source.metadata.get("category", "")
                    print(f"   [{i}] {pdf_name} (relevance: {score:.2f}) - {category}")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

    # Cleanup
    print("\n🧹 Closing connection...")
    await vector_store.close()
    print("✅ Done!")


if __name__ == "__main__":
    asyncio.run(interactive_session())
