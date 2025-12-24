#!/usr/bin/env python3
"""
Incremental PDF ingestion for large files.

Processes PDFs page-by-page in small batches to avoid overwhelming the system.
Supports resume capability - tracks progress and can continue from where it left off.

Usage:
    python scripts/ingest_large_pdf.py <pdf_path> [--pages-per-batch 5] [--start-page 0]
"""

import argparse
import asyncio
import hashlib
import json
import sys
import time
from pathlib import Path

import asyncpg
import pymupdf4llm

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.embeddings.ollama_embedder import OllamaEmbedder
from calculus_rag.vectorstore.pgvector_store import PgVectorStore


# Progress tracking file
PROGRESS_FILE = Path(__file__).parent.parent / ".ingestion_progress.json"


def load_progress() -> dict:
    """Load ingestion progress from file."""
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {}


def save_progress(progress: dict):
    """Save ingestion progress to file."""
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


def get_pdf_hash(pdf_path: Path) -> str:
    """Get hash of PDF file for tracking."""
    return hashlib.md5(pdf_path.read_bytes()[:1024]).hexdigest()[:8]


def extract_pages(pdf_path: Path, start_page: int, num_pages: int) -> list[dict]:
    """Extract specific pages from PDF as markdown chunks."""
    import fitz  # pymupdf

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    end_page = min(start_page + num_pages, total_pages)

    chunks = []

    for page_num in range(start_page, end_page):
        # Extract single page as markdown
        page_md = pymupdf4llm.to_markdown(
            pdf_path,
            pages=[page_num],
            show_progress=False,
        )

        if page_md and page_md.strip():
            # Split page into smaller chunks if too large
            page_chunks = split_text(page_md, chunk_size=512, overlap=50)
            for i, chunk_text in enumerate(page_chunks):
                if chunk_text.strip():
                    chunks.append({
                        "content": chunk_text,
                        "page": page_num + 1,  # 1-indexed for display
                        "chunk_index": i,
                    })

    doc.close()
    return chunks, total_pages


def split_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Split text into chunks with overlap."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('. ')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            if break_point > chunk_size // 2:
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1

        chunks.append(chunk.strip())
        start = end - overlap

    return [c for c in chunks if c]


def get_category(pdf_name: str) -> str:
    """Determine category based on PDF name."""
    name_lower = pdf_name.lower()
    if "solution" in name_lower:
        return "Solutions"
    elif "calculus_1" in name_lower or "calculus1" in name_lower:
        return "Calculus 1"
    elif "calculus_2" in name_lower or "calculus2" in name_lower:
        return "Calculus 2"
    elif "calculus" in name_lower:
        return "Calculus"
    return "Reference"


async def ingest_batch(
    vector_store: PgVectorStore,
    embedder: OllamaEmbedder,
    chunks: list[dict],
    pdf_name: str,
    category: str,
) -> int:
    """Ingest a batch of chunks into the vector store."""
    if not chunks:
        return 0

    # Prepare batch data
    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for chunk in chunks:
        try:
            # Generate embedding
            embedding = embedder.embed(chunk["content"])

            # Create unique ID
            chunk_id = f"{pdf_name}_p{chunk['page']}_c{chunk['chunk_index']}_{hash(chunk['content']) % 10000}"

            # Create metadata
            metadata = {
                "source": pdf_name,
                "page": chunk["page"],
                "chunk_index": chunk["chunk_index"],
                "category": category,
                "content_type": "pdf",
            }

            ids.append(chunk_id)
            embeddings.append(embedding)
            documents.append(chunk["content"])
            metadatas.append(metadata)

        except Exception as e:
            print(f"    Warning: Failed to embed chunk: {e}")

    # Batch insert into vector store
    if ids:
        try:
            await vector_store.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            return len(ids)
        except Exception as e:
            print(f"    Warning: Failed to insert batch: {e}")
            return 0

    return 0


async def main():
    parser = argparse.ArgumentParser(description="Ingest large PDFs incrementally")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("--pages-per-batch", type=int, default=5, help="Pages to process per batch")
    parser.add_argument("--start-page", type=int, default=None, help="Start from specific page (0-indexed)")
    parser.add_argument("--reset", action="store_true", help="Reset progress and start fresh")
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    pdf_name = pdf_path.name
    pdf_hash = get_pdf_hash(pdf_path)
    progress_key = f"{pdf_name}_{pdf_hash}"

    # Load or reset progress
    progress = load_progress()
    if args.reset and progress_key in progress:
        del progress[progress_key]
        save_progress(progress)
        print(f"Reset progress for {pdf_name}")

    # Determine starting page
    if args.start_page is not None:
        start_page = args.start_page
    elif progress_key in progress:
        start_page = progress[progress_key].get("last_page", 0)
        print(f"Resuming from page {start_page + 1}")
    else:
        start_page = 0

    print(f"\n{'='*60}")
    print(f"Incremental PDF Ingestion")
    print(f"{'='*60}")
    print(f"PDF: {pdf_name}")
    print(f"Size: {pdf_path.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"Batch size: {args.pages_per_batch} pages")
    print(f"Starting from page: {start_page + 1}")
    print(f"{'='*60}\n")

    # Initialize components
    settings = get_settings()

    print("Initializing embedder...")
    embedder = OllamaEmbedder(
        model=settings.embedding_model_name,
        base_url=settings.ollama_base_url,
        dimension=settings.vector_dimension,
    )

    print("Connecting to database...")
    vector_store = PgVectorStore(
        connection_string=settings.postgres_dsn,
        dimension=settings.vector_dimension,
        table_name="calculus_knowledge",
    )
    await vector_store.initialize()

    # Get total pages
    import fitz
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()
    print(f"Total pages in PDF: {total_pages}\n")

    category = get_category(pdf_name)
    total_chunks = 0
    current_page = start_page

    try:
        while current_page < total_pages:
            batch_start = time.time()
            end_page = min(current_page + args.pages_per_batch, total_pages)

            print(f"Processing pages {current_page + 1}-{end_page} of {total_pages}...", end=" ", flush=True)

            # Extract pages
            chunks, _ = extract_pages(pdf_path, current_page, args.pages_per_batch)

            # Ingest batch
            ingested = await ingest_batch(vector_store, embedder, chunks, pdf_name, category)
            total_chunks += ingested

            batch_time = time.time() - batch_start
            print(f"{ingested} chunks ({batch_time:.1f}s)")

            # Save progress
            current_page = end_page
            progress[progress_key] = {
                "last_page": current_page,
                "total_pages": total_pages,
                "chunks_ingested": progress.get(progress_key, {}).get("chunks_ingested", 0) + ingested,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            save_progress(progress)

            # Brief pause to avoid overwhelming system
            if current_page < total_pages:
                await asyncio.sleep(0.5)

    except KeyboardInterrupt:
        print(f"\n\nInterrupted! Progress saved at page {current_page}")
        print(f"Resume with: python scripts/ingest_large_pdf.py {pdf_path}")

    finally:
        await vector_store.close()

    print(f"\n{'='*60}")
    print(f"Ingestion Complete!")
    print(f"{'='*60}")
    print(f"Pages processed: {current_page} / {total_pages}")
    print(f"Chunks ingested this session: {total_chunks}")
    print(f"Total chunks for this PDF: {progress.get(progress_key, {}).get('chunks_ingested', total_chunks)}")

    # Show cache stats
    print(f"\nEmbedding cache stats: {embedder.cache_stats}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
