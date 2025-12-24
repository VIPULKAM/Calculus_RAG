#!/usr/bin/env python3
"""
Batch cleanup of corrupted chunks in the database.

Finds chunks with corruption markers and updates them in-place
using the cleanup_math_text function.

Usage:
    python scripts/cleanup_corrupted_chunks.py [--dry-run] [--batch-size 100]
"""

import argparse
import asyncio
import sys
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.utils.text_cleanup import cleanup_math_text


async def find_corrupted_chunks(conn: asyncpg.Connection) -> list[dict]:
    """Find all chunks with corruption markers."""
    query = """
        SELECT id, content, metadata->>'source' as source
        FROM calculus_knowledge
        WHERE content LIKE '%⎡%'
           OR content LIKE '%⎤%'
           OR content LIKE '%⎣%'
           OR content LIKE '%⎦%'
           OR content LIKE '%~~%'
           OR content LIKE '%_x_%'
           OR content LIKE '%_a_%'
           OR content LIKE '%_b_%'
           OR content LIKE '%_f_%'
           OR content LIKE '%_t_%'
           OR content LIKE '%OpenStax%'
    """
    rows = await conn.fetch(query)
    return [dict(row) for row in rows]


async def update_chunk(conn: asyncpg.Connection, chunk_id: str, cleaned_content: str) -> bool:
    """Update a single chunk with cleaned content."""
    try:
        await conn.execute(
            "UPDATE calculus_knowledge SET content = $1 WHERE id = $2",
            cleaned_content,
            chunk_id
        )
        return True
    except Exception as e:
        print(f"  Error updating {chunk_id}: {e}")
        return False


async def main():
    parser = argparse.ArgumentParser(description="Cleanup corrupted chunks in database")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned without updating")
    parser.add_argument("--batch-size", type=int, default=100, help="Chunks to process per batch")
    parser.add_argument("--show-examples", type=int, default=3, help="Number of before/after examples to show")
    args = parser.parse_args()

    settings = get_settings()

    print("="*70)
    print("Batch Cleanup of Corrupted Chunks")
    print("="*70)
    print(f"Mode: {'DRY RUN (no changes)' if args.dry_run else 'LIVE (will update database)'}")
    print(f"Batch size: {args.batch_size}")
    print("="*70)

    conn = await asyncpg.connect(settings.postgres_dsn)

    # Get total count first
    total_count = await conn.fetchval("SELECT COUNT(*) FROM calculus_knowledge")
    print(f"\nTotal chunks in database: {total_count:,}")

    # Find corrupted chunks
    print("\nFinding corrupted chunks...")
    corrupted = await find_corrupted_chunks(conn)
    print(f"Found {len(corrupted):,} chunks with corruption markers")

    if not corrupted:
        print("\nNo corrupted chunks found!")
        await conn.close()
        return

    # Group by source for reporting
    by_source = {}
    for chunk in corrupted:
        source = chunk['source'] or 'Unknown'
        by_source[source] = by_source.get(source, 0) + 1

    print("\nCorruption by source:")
    for source, count in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"  {count:>5} - {source}")

    # Show examples
    print(f"\n{'='*70}")
    print(f"BEFORE/AFTER EXAMPLES ({args.show_examples} samples)")
    print("="*70)

    for i, chunk in enumerate(corrupted[:args.show_examples]):
        original = chunk['content']
        cleaned = cleanup_math_text(original)

        print(f"\n--- Example {i+1} ({chunk['source']}) ---")
        print(f"BEFORE ({len(original)} chars):")
        print(original[:300] + "..." if len(original) > 300 else original)
        print(f"\nAFTER ({len(cleaned)} chars):")
        print(cleaned[:300] + "..." if len(cleaned) > 300 else cleaned)
        print("-"*40)

    if args.dry_run:
        print(f"\n{'='*70}")
        print("DRY RUN COMPLETE - No changes made")
        print(f"Would update {len(corrupted):,} chunks")
        print("Run without --dry-run to apply changes")
        print("="*70)
        await conn.close()
        return

    # Confirm before proceeding
    print(f"\n{'='*70}")
    print(f"Ready to update {len(corrupted):,} chunks")
    print("="*70)

    confirm = input("Proceed with cleanup? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Aborted.")
        await conn.close()
        return

    # Process in batches
    print(f"\nProcessing {len(corrupted):,} chunks...")

    updated = 0
    failed = 0

    for i in range(0, len(corrupted), args.batch_size):
        batch = corrupted[i:i + args.batch_size]

        for chunk in batch:
            cleaned = cleanup_math_text(chunk['content'])

            # Only update if content actually changed
            if cleaned != chunk['content']:
                success = await update_chunk(conn, chunk['id'], cleaned)
                if success:
                    updated += 1
                else:
                    failed += 1

        progress = min(i + args.batch_size, len(corrupted))
        print(f"  Processed {progress:,}/{len(corrupted):,} ({progress*100//len(corrupted)}%)")

    print(f"\n{'='*70}")
    print("CLEANUP COMPLETE")
    print("="*70)
    print(f"Chunks updated: {updated:,}")
    print(f"Chunks failed: {failed:,}")
    print(f"Chunks unchanged: {len(corrupted) - updated - failed:,}")
    print("="*70)

    # Verify
    remaining = await find_corrupted_chunks(conn)
    print(f"\nVerification: {len(remaining):,} chunks still have corruption markers")

    if remaining:
        print("(Some patterns may need additional cleanup rules)")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
