#!/usr/bin/env python3
"""
Add a single PDF to the knowledge base WITHOUT clearing existing data.

Usage:
    python scripts/add_pdf.py path/to/your/file.pdf

Example:
    python scripts/add_pdf.py ~/Downloads/S1_Final_Review.pdf
"""

import asyncio
import sys
from pathlib import Path

import asyncpg

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.embeddings.ollama_embedder import OllamaEmbedder
from calculus_rag.vectorstore.pgvector_store import PgVectorStore
from calculus_rag.loaders.pymupdf_loader import PyMuPDFLoader


async def add_single_pdf(pdf_path: str) -> int:
    """
    Add a single PDF to the knowledge base.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Number of chunks added
    """
    pdf_file = Path(pdf_path).expanduser().resolve()

    # Validate file exists
    if not pdf_file.exists():
        print(f"❌ Error: File not found: {pdf_file}")
        return 0

    if not pdf_file.suffix.lower() == '.pdf':
        print(f"❌ Error: Not a PDF file: {pdf_file}")
        return 0

    print(f"\n{'='*60}")
    print(f"Adding PDF to Knowledge Base")
    print(f"{'='*60}\n")
    print(f"📄 File: {pdf_file.name}")
    print(f"📁 Path: {pdf_file}")
    print(f"📊 Size: {pdf_file.stat().st_size / 1024 / 1024:.1f} MB\n")

    # Initialize components
    settings = get_settings()

    print("[1/4] Loading embedding model...")
    embedder = OllamaEmbedder(
        model=settings.embedding_model_name,
        base_url=settings.ollama_base_url,
        dimension=settings.vector_dimension,
    )
    print(f"   ✓ Loaded: {settings.embedding_model_name}")

    print("\n[2/4] Connecting to database...")
    vector_store = PgVectorStore(
        connection_string=settings.postgres_dsn,
        dimension=settings.vector_dimension,
        table_name="calculus_knowledge",
    )
    await vector_store.initialize()

    # Check current count using asyncpg directly
    conn = await asyncpg.connect(settings.postgres_dsn)
    current_count = await conn.fetchval("SELECT COUNT(*) FROM calculus_knowledge")
    print(f"   ✓ Connected (current chunks: {current_count})")

    print("\n[3/4] Processing PDF...")
    pdf_loader = PyMuPDFLoader(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    documents = pdf_loader.load(pdf_file)
    print(f"   ✓ Extracted {len(documents)} chunks")

    if len(documents) == 0:
        print("   ⚠️ No text extracted from PDF")
        return 0

    print("\n[4/4] Adding to knowledge base...")

    # Prepare data for ingestion
    ids = []
    embeddings = []
    texts = []
    metadatas = []

    for i, doc in enumerate(documents):
        chunk_id = f"{pdf_file.stem}_{i}"
        content = doc.get("content", "")

        # Generate embedding
        print(f"   Embedding chunk {i+1}/{len(documents)}...", end="\r")
        embedding = embedder.embed(content)

        ids.append(chunk_id)
        embeddings.append(embedding)
        texts.append(content)
        metadatas.append({
            "source": pdf_file.name,
            "chunk_index": i,
            "total_chunks": len(documents),
            "category": "user_added",
        })

    # Add to vector store
    await vector_store.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    # Verify final count
    new_count = await conn.fetchval("SELECT COUNT(*) FROM calculus_knowledge")
    added = new_count - current_count

    # Clean up
    await conn.close()
    await vector_store.close()

    print(f"\n\n{'='*60}")
    print(f"✅ Successfully added {added} chunks from {pdf_file.name}")
    print(f"   Total chunks in database: {new_count}")
    print(f"{'='*60}\n")

    return added


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("❌ Error: Please provide a PDF file path")
        print("\nExample:")
        print("  python scripts/add_pdf.py ~/Downloads/my_notes.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    try:
        chunks_added = asyncio.run(add_single_pdf(pdf_path))
        if chunks_added > 0:
            print("🎉 Done! You can now ask questions about this content.")
        sys.exit(0 if chunks_added > 0 else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
