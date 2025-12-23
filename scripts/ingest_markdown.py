#!/usr/bin/env python3
"""
Ingest markdown files into the pgvector knowledge base.

Processes markdown files from knowledge_content/ and adds them to the vector store.
"""

import asyncio
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.embeddings.ollama_embedder import OllamaEmbedder
from calculus_rag.vectorstore.pgvector_store import PgVectorStore


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown content."""
    import yaml

    if not content.startswith("---"):
        return {}, content

    # Find the closing ---
    end_idx = content.find("---", 3)
    if end_idx == -1:
        return {}, content

    frontmatter_str = content[3:end_idx].strip()
    body = content[end_idx + 3:].strip()

    try:
        metadata = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError:
        metadata = {}

    return metadata, body


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence/paragraph boundary
        if end < len(text):
            # Look for paragraph break first
            para_break = text.rfind("\n\n", start, end)
            if para_break > start + chunk_size // 2:
                end = para_break + 2
            else:
                # Look for sentence break
                for sep in [". ", ".\n", "! ", "? "]:
                    sent_break = text.rfind(sep, start, end)
                    if sent_break > start + chunk_size // 2:
                        end = sent_break + len(sep)
                        break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap if end < len(text) else len(text)

    return chunks


async def ingest_markdown_files(directory: Path, category: str = "khan_academy"):
    """Ingest all markdown files from a directory."""

    settings = get_settings()

    print("=" * 70)
    print(f"INGESTING MARKDOWN FILES: {directory}")
    print("=" * 70)

    # Initialize embedder
    print("\n📦 Initializing embedder...")
    embedder = OllamaEmbedder(
        model=settings.embedding_model_name,
        base_url=settings.ollama_base_url,
        dimension=settings.vector_dimension,
    )

    # Initialize vector store
    print("📦 Initializing vector store...")
    vector_store = PgVectorStore(
        connection_string=settings.postgres_dsn,
        dimension=settings.vector_dimension,
        table_name="calculus_knowledge",
    )
    await vector_store.initialize()

    # Find all markdown files
    md_files = list(directory.glob("**/*.md"))
    print(f"\n📄 Found {len(md_files)} markdown files")

    total_chunks = 0
    successful_files = 0

    for md_file in md_files:
        print(f"\n📝 Processing: {md_file.name}")

        # Read file
        content = md_file.read_text(encoding="utf-8")

        # Parse frontmatter
        metadata, body = parse_frontmatter(content)

        if not body.strip():
            print(f"  ⚠️  Empty content, skipping")
            continue

        # Chunk the content
        chunks = chunk_text(body, chunk_size=512, overlap=50)
        print(f"  📦 {len(chunks)} chunks")

        # Prepare data for insertion
        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            # Create unique ID
            chunk_id = hashlib.md5(f"{md_file.name}:{i}:{chunk[:50]}".encode()).hexdigest()

            # Get embedding
            embedding = embedder.embed(chunk)

            # Build metadata
            chunk_metadata = {
                "source": md_file.name,
                "category": category,
                "topic": metadata.get("topic", "precalculus"),
                "difficulty": metadata.get("difficulty", 2),
                "source_type": "markdown",
                "content_type": metadata.get("content_type", "video_summary"),
                "chunk_index": i,
                "total_chunks": len(chunks),
                "video_id": metadata.get("video_id", ""),
                "source_url": metadata.get("source_url", ""),
            }

            ids.append(chunk_id)
            embeddings.append(embedding)
            documents.append(chunk)
            metadatas.append(chunk_metadata)

        # Add to vector store
        await vector_store.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        total_chunks += len(chunks)
        successful_files += 1
        print(f"  ✅ Added {len(chunks)} chunks")

    await vector_store.close()

    print("\n" + "=" * 70)
    print("INGESTION COMPLETE")
    print("=" * 70)
    print(f"✅ Files processed: {successful_files}/{len(md_files)}")
    print(f"📦 Total chunks added: {total_chunks}")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Ingest markdown files into pgvector")
    parser.add_argument(
        "--dir",
        type=str,
        default="knowledge_content/khan_academy",
        help="Directory containing markdown files",
    )
    parser.add_argument(
        "--category",
        type=str,
        default="khan_academy",
        help="Category label for the content",
    )
    args = parser.parse_args()

    directory = Path(__file__).parent.parent / args.dir
    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        return

    await ingest_markdown_files(directory, args.category)


if __name__ == "__main__":
    asyncio.run(main())
