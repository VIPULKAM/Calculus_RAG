#!/usr/bin/env python3
"""
PDF Knowledge Base Ingestion Script

This script:
1. Organizes PDFs from ~/Downloads into categorized folders
2. Extracts text and creates chunks
3. Generates embeddings
4. Stores everything in pgvector

Usage: python scripts/ingest_pdfs.py
"""

import asyncio
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.embeddings.bge_embedder import BGEEmbedder
from calculus_rag.embeddings.ollama_embedder import OllamaEmbedder
from calculus_rag.loaders.pymupdf_loader import PyMuPDFLoader
from calculus_rag.vectorstore.pgvector_store import PgVectorStore


# PDF Categorization Rules
CATEGORY_RULES = {
    "pre_calculus/algebra": [
        r"algebra",
        r"algebraic",
    ],
    "pre_calculus/trigonometry": [
        r"trig",
        r"trigonometry",
    ],
    "pre_calculus/functions": [
        r"function",
    ],
    "calculus/limits": [
        r"limit",
    ],
    "calculus/derivatives": [
        r"derivative",
        r"differentiation",
    ],
    "calculus/integration": [
        r"integral",
        r"integration",
    ],
    "calculus": [
        r"calculus",
    ],
    "reference": [
        r"cheat",
        r"common",
        r"table",
        r"sheet",
    ],
    "practice": [
        r"problem",
        r"solution",
        r"assignment",
    ],
    "guides": [
        r"study",
        r"error",
        r"primer",
    ],
}


def categorize_pdf(filename: str) -> str:
    """
    Auto-categorize PDF based on filename.

    Args:
        filename: Name of the PDF file

    Returns:
        Category path (e.g., "calculus/derivatives")
    """
    filename_lower = filename.lower()

    # Check each category
    for category, patterns in CATEGORY_RULES.items():
        for pattern in patterns:
            if re.search(pattern, filename_lower):
                return category

    # Default to calculus if can't categorize
    return "calculus"


def organize_pdfs(source_dir: Path, target_dir: Path) -> dict[str, list[Path]]:
    """
    Copy and organize PDFs from source to target directory.

    Args:
        source_dir: Source directory (e.g., ~/Downloads)
        target_dir: Target directory (knowledge_content/)

    Returns:
        Dictionary mapping categories to list of PDF paths
    """
    print("=" * 80)
    print("PDF Organization")
    print("=" * 80)

    # Find all PDFs
    pdf_files = list(source_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"\n❌ No PDF files found in {source_dir}")
        return {}

    print(f"\n📚 Found {len(pdf_files)} PDF files")

    organized = {}

    for pdf_file in pdf_files:
        # Skip duplicates (files with -1 suffix)
        if "-1.pdf" in pdf_file.name or "_-_WEB" in pdf_file.name:
            print(f"   ⏭️  Skipping duplicate: {pdf_file.name}")
            continue

        # Skip advanced topics (diff eq, etc.) for high school
        if "DiffEQ" in pdf_file.name:
            print(f"   ⏭️  Skipping advanced: {pdf_file.name}")
            continue

        # Categorize
        category = categorize_pdf(pdf_file.name)
        category_path = target_dir / category

        # Create category directory
        category_path.mkdir(parents=True, exist_ok=True)

        # Copy file
        dest_path = category_path / pdf_file.name
        if not dest_path.exists():
            shutil.copy2(pdf_file, dest_path)
            print(f"   ✓ {pdf_file.name} → {category}/")

            # Track organized files
            if category not in organized:
                organized[category] = []
            organized[category].append(dest_path)
        else:
            print(f"   ⏭️  Already exists: {category}/{pdf_file.name}")
            if category not in organized:
                organized[category] = []
            organized[category].append(dest_path)

    print(f"\n✅ Organized {sum(len(files) for files in organized.values())} PDFs into {len(organized)} categories")
    return organized


async def ingest_pdfs(
    pdf_files: list[Path],
    embedder: BGEEmbedder,
    vector_store: PgVectorStore,
    pdf_loader: PyMuPDFLoader,
) -> int:
    """
    Ingest PDF files into the vector store.

    Args:
        pdf_files: List of PDF file paths
        embedder: Embedder instance
        vector_store: Vector store instance
        pdf_loader: PDF loader instance

    Returns:
        Total number of chunks ingested
    """
    total_chunks = 0

    for pdf_file in pdf_files:
        print(f"\n📖 Processing: {pdf_file.name}")

        try:
            # Load and chunk PDF
            documents = pdf_loader.load(pdf_file)
            print(f"   ├─ Extracted {len(documents)} chunks")

            # Prepare batch data
            ids = []
            embeddings = []
            contents = []
            metadatas = []

            for i, doc in enumerate(documents):
                chunk_id = f"{pdf_file.stem}_{i}"
                content = doc["content"]

                # Add category metadata from file path
                category = "/".join(pdf_file.parent.relative_to(pdf_file.parent.parent.parent).parts)
                doc["metadata"]["category"] = category
                doc["metadata"]["topic"] = category.replace("/", ".")

                # Determine difficulty based on category
                if "pre_calculus" in category:
                    doc["metadata"]["difficulty"] = 2
                elif "reference" in category or "guides" in category:
                    doc["metadata"]["difficulty"] = 1
                elif "calculus" in category:
                    doc["metadata"]["difficulty"] = 3
                else:
                    doc["metadata"]["difficulty"] = 2

                ids.append(chunk_id)
                contents.append(content)
                metadatas.append(doc["metadata"])

            # Generate embeddings (batch)
            print(f"   ├─ Generating embeddings...")
            for content in contents:
                embedding = embedder.embed(content)
                embeddings.append(embedding)

            # Store in vector database
            print(f"   ├─ Storing in vector database...")
            await vector_store.add(
                ids=ids,
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas,
            )

            print(f"   └─ ✅ Ingested {len(documents)} chunks from {pdf_file.name}")
            total_chunks += len(documents)

        except Exception as e:
            print(f"   └─ ❌ Error processing {pdf_file.name}: {e}")
            import traceback

            traceback.print_exc()

    return total_chunks


async def main():
    """Main ingestion pipeline."""
    print("=" * 80)
    print("Calculus RAG - PDF Knowledge Base Ingestion")
    print("=" * 80)

    settings = get_settings()

    # Step 1: Organize PDFs
    source_dir = Path.home() / "Downloads"
    target_dir = Path("./knowledge_content")

    organized_pdfs = organize_pdfs(source_dir, target_dir)

    if not organized_pdfs:
        print("\n❌ No PDFs to ingest. Exiting.")
        return

    # Show summary
    print("\n" + "=" * 80)
    print("Organization Summary")
    print("=" * 80)
    for category, files in sorted(organized_pdfs.items()):
        print(f"\n📁 {category}/ ({len(files)} files)")
        for file in sorted(files):
            print(f"   • {file.name}")

    # Step 2: Initialize components
    print("\n" + "=" * 80)
    print("Initializing Components")
    print("=" * 80)

    print("\n[1/3] Loading Embedder...")
    if settings.embedding_type == "ollama":
        embedder = OllamaEmbedder(
            model=settings.embedding_model_name,
            base_url=settings.ollama_base_url,
            dimension=settings.vector_dimension,
        )
        print(f"   ✓ Loaded Ollama embedder: {settings.embedding_model_name}")
    else:
        embedder = BGEEmbedder(
            model_name=settings.embedding_model_name,
            device=settings.embedding_device,
        )
        print(f"   ✓ Loaded BGE embedder: {settings.embedding_model_name}")
    print(f"   ✓ Embedding dimension: {embedder.dimension}")

    print("\n[2/3] Connecting to Vector Store...")
    vector_store = PgVectorStore(
        connection_string=settings.postgres_dsn,
        dimension=settings.vector_dimension,
        table_name="calculus_knowledge",
    )
    await vector_store.initialize()
    print("   ✓ Connected")

    # Clear existing data
    print("\n[3/3] Clearing existing knowledge base...")
    await vector_store.delete_all()
    print("   ✓ Cleared")

    # Step 3: Ingest PDFs (prioritize smaller, more focused files)
    print("\n" + "=" * 80)
    print("PDF Ingestion (Processing by Priority)")
    print("=" * 80)

    pdf_loader = PyMuPDFLoader(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    # Collect all PDFs with file sizes
    all_pdfs = []
    skipped_large = []
    MAX_SIZE_MB = 15  # Skip files larger than 15MB for now

    for files in organized_pdfs.values():
        for pdf_file in files:
            size = pdf_file.stat().st_size
            size_mb = size / (1024 * 1024)

            if size_mb > MAX_SIZE_MB:
                skipped_large.append((pdf_file, size_mb))
            else:
                all_pdfs.append((pdf_file, size))

    # Sort by size (process smaller files first to avoid OOM)
    all_pdfs.sort(key=lambda x: x[1])

    if skipped_large:
        print(f"\n⏭️  Skipping {len(skipped_large)} large files (>{MAX_SIZE_MB}MB):")
        for pdf_file, size_mb in skipped_large:
            print(f"   • {pdf_file.name} ({size_mb:.1f} MB)")
        print(f"\n💡 Process these separately later if needed")

    print(f"\n📋 Processing order (smallest to largest):")
    for pdf_file, size in all_pdfs:
        size_mb = size / (1024 * 1024)
        print(f"   • {pdf_file.name} ({size_mb:.1f} MB)")

    # Process one at a time to manage memory
    total_chunks = 0
    for i, (pdf_file, _) in enumerate(all_pdfs, 1):
        print(f"\n{'=' * 80}")
        print(f"PDF {i}/{len(all_pdfs)}")
        print(f"{'=' * 80}")

        chunks = await ingest_pdfs([pdf_file], embedder, vector_store, pdf_loader)
        total_chunks += chunks

        # Show progress
        print(f"\n📊 Progress: {i}/{len(all_pdfs)} PDFs, {total_chunks} total chunks ingested")

    # Summary
    print("\n" + "=" * 80)
    print("Ingestion Complete!")
    print("=" * 80)
    print(f"\n📊 Statistics:")
    print(f"   • Total PDFs processed: {len(all_pdfs)}")
    print(f"   • Total chunks created: {total_chunks}")
    print(f"   • Categories: {len(organized_pdfs)}")
    print(f"   • Vector dimension: {embedder.dimension}")
    print(f"   • Database table: calculus_knowledge")

    print("\n✅ Knowledge base is ready!")
    print("\n💡 Next steps:")
    print("   • Test with: python scripts/interactive_rag.py")
    print("   • Query with: python scripts/test_rag_quick.py")

    # Cleanup
    await vector_store.close()


if __name__ == "__main__":
    asyncio.run(main())
