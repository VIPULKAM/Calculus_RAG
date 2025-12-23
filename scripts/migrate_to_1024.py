#!/usr/bin/env python3
"""
Migrate database from 768 to 1024 dimensions.

This drops the old table and recreates it with the new dimension.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings


async def main():
    """Drop old table and prepare for new 1024-d embeddings."""
    print("=" * 80)
    print("Migrating to 1024-dimensional embeddings (mxbai-embed-large)")
    print("=" * 80)

    settings = get_settings()

    print(f"\nConnecting to database: {settings.postgres_db}")

    import asyncpg

    conn = await asyncpg.connect(settings.postgres_dsn)

    # Drop old table
    print("\n[1/2] Dropping old 768-dimensional table...")
    await conn.execute("DROP TABLE IF EXISTS calculus_knowledge CASCADE;")
    print("   ✓ Old table dropped")

    # Create new table with 1024 dimensions
    print("\n[2/2] Creating new 1024-dimensional table...")
    await conn.execute(f"""
        CREATE TABLE IF NOT EXISTS calculus_knowledge (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            document_id TEXT,
            chunk_index INTEGER,
            metadata JSONB,
            embedding vector({settings.vector_dimension})
        );
    """)
    print(f"   ✓ New table created with dimension={settings.vector_dimension}")

    # Create index
    print("\n[3/3] Creating vector index...")
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS calculus_knowledge_embedding_idx
        ON calculus_knowledge
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)
    print("   ✓ Vector index created")

    await conn.close()

    print("\n" + "=" * 80)
    print("✅ Migration Complete!")
    print("=" * 80)
    print("\n💡 Next step: Run ingestion script")
    print("   python scripts/ingest_pdfs.py")


if __name__ == "__main__":
    asyncio.run(main())
