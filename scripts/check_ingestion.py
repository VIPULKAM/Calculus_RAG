#!/usr/bin/env python3
"""Check ingestion status in the database."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.vectorstore.pgvector_store import PgVectorStore


async def main():
    """Check what's in the database."""
    settings = get_settings()

    vector_store = PgVectorStore(
        connection_string=settings.postgres_dsn,
        dimension=settings.vector_dimension,
        table_name="calculus_knowledge",
    )

    await vector_store.initialize()

    # Get total count
    import asyncpg

    conn = await asyncpg.connect(settings.postgres_dsn)

    # Count total chunks
    total = await conn.fetchval("SELECT COUNT(*) FROM calculus_knowledge")
    print(f"\n📊 Database Statistics")
    print("=" * 80)
    print(f"Total chunks ingested: {total}")

    # Get unique sources
    sources = await conn.fetch(
        "SELECT metadata->>'source' as source, COUNT(*) as chunks "
        "FROM calculus_knowledge "
        "GROUP BY metadata->>'source' "
        "ORDER BY chunks DESC"
    )

    print(f"\n📚 PDFs Ingested ({len(sources)} files):")
    print("-" * 80)
    for row in sources:
        print(f"  • {row['source']}: {row['chunks']} chunks")

    # Get categories
    categories = await conn.fetch(
        "SELECT metadata->>'category' as category, COUNT(*) as chunks "
        "FROM calculus_knowledge "
        "GROUP BY metadata->>'category' "
        "ORDER BY chunks DESC"
    )

    print(f"\n📁 Categories:")
    print("-" * 80)
    for row in categories:
        print(f"  • {row['category']}: {row['chunks']} chunks")

    await conn.close()
    await vector_store.close()

    print("\n✅ Knowledge base is ready to use!")


if __name__ == "__main__":
    asyncio.run(main())
