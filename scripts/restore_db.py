#!/usr/bin/env python3
"""
Fast restore of the knowledge base using parallel pg_restore.

Usage:
    python scripts/restore_db.py backups/backup_2025-12-23.dump.gz
    python scripts/restore_db.py backups/backup_2025-12-23.dump --jobs 8

Supports both .dump and .dump.gz (gzipped) backup files.

WARNING: This will REPLACE all existing data in the knowledge base!
"""

import argparse
import gzip
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from calculus_rag.config import get_settings


def get_cpu_count() -> int:
    """Get number of CPUs for parallel processing."""
    try:
        return os.cpu_count() or 4
    except:
        return 4


def restore_database(backup_file: str, jobs: int = None, force: bool = False) -> bool:
    """
    Fast parallel restore from binary dump.

    Args:
        backup_file: Path to .dump or .dump.gz file
        jobs: Number of parallel jobs
        force: Skip confirmation prompt

    Returns:
        True if successful
    """
    settings = get_settings()
    jobs = jobs or get_cpu_count()

    backup_path = Path(backup_file)

    # Check in backups/ directory if not found
    if not backup_path.exists():
        backup_path = Path(__file__).parent.parent / "backups" / backup_file

    if not backup_path.exists():
        print(f"❌ Backup file not found: {backup_file}")
        print(f"\n📚 Available backups:")
        backup_dir = Path(__file__).parent.parent / "backups"
        backups = list(backup_dir.glob("*.dump")) + list(backup_dir.glob("*.dump.gz"))
        for b in sorted(backups, key=lambda f: f.stat().st_mtime, reverse=True)[:5]:
            print(f"   • {b.name}")
        return False

    size_mb = backup_path.stat().st_size / 1024 / 1024
    is_gzipped = backup_path.suffix == ".gz"

    print(f"\n{'='*60}")
    print(f"Fast Database Restore (Parallel)")
    print(f"{'='*60}\n")
    print(f"📄 Backup: {backup_path.name}")
    print(f"📊 Size: {size_mb:.2f} MB" + (" (gzipped)" if is_gzipped else ""))
    print(f"📦 Target: {settings.postgres_db}")
    print(f"🖥️  Parallel jobs: {jobs}")

    # Confirmation
    if not force:
        print(f"\n⚠️  WARNING: This will REPLACE all existing data!")
        response = input("   Continue? (yes/no): ").strip().lower()
        if response != "yes":
            print("   Cancelled.")
            return False

    env = {"PGPASSWORD": settings.postgres_password}
    temp_file = None

    # Decompress if gzipped
    if is_gzipped:
        print(f"\n⏳ Decompressing backup...")
        temp_file = tempfile.NamedTemporaryFile(suffix=".dump", delete=False)
        with gzip.open(backup_path, 'rb') as f_in:
            shutil.copyfileobj(f_in, temp_file)
        temp_file.close()
        restore_path = Path(temp_file.name)
        print(f"   Decompressed: {restore_path.stat().st_size / 1024 / 1024:.2f} MB")
    else:
        restore_path = backup_path

    # Step 1: Drop and recreate the table
    print(f"\n⏳ Step 1/2: Preparing database...")

    drop_cmd = [
        "psql",
        "-h", settings.postgres_host,
        "-p", str(settings.postgres_port),
        "-U", settings.postgres_user,
        "-d", settings.postgres_db,
        "-c", "DROP TABLE IF EXISTS calculus_knowledge CASCADE;"
    ]

    subprocess.run(drop_cmd, env={**os.environ, **env}, capture_output=True)

    # Step 2: Restore
    print(f"⏳ Step 2/2: Restoring data (parallel)...")
    start = datetime.now()

    restore_cmd = [
        "pg_restore",
        "-h", settings.postgres_host,
        "-p", str(settings.postgres_port),
        "-U", settings.postgres_user,
        "-d", settings.postgres_db,
        "-j", str(jobs),          # Parallel jobs
        "--no-owner",
        "--no-acl",
        "--clean",                # Drop objects before recreating
        "--if-exists",            # Don't error if objects don't exist
        str(restore_path),
    ]

    try:
        result = subprocess.run(
            restore_cmd,
            env={**os.environ, **env},
            capture_output=True,
            text=True,
        )

        elapsed = (datetime.now() - start).total_seconds()

        # pg_restore may return warnings, check if data was restored
        if result.returncode != 0 and "error" in result.stderr.lower():
            print(f"❌ Restore failed: {result.stderr}")
            return False

        # Verify restoration
        verify_cmd = [
            "psql",
            "-h", settings.postgres_host,
            "-p", str(settings.postgres_port),
            "-U", settings.postgres_user,
            "-d", settings.postgres_db,
            "-t", "-c", "SELECT COUNT(*) FROM calculus_knowledge;"
        ]

        verify_result = subprocess.run(
            verify_cmd,
            env={**os.environ, **env},
            capture_output=True,
            text=True,
        )

        chunk_count = verify_result.stdout.strip() if verify_result.returncode == 0 else "?"

        print(f"\n✅ Restore complete!")
        print(f"   📊 Chunks restored: {chunk_count}")
        print(f"   ⏱️  Time: {elapsed:.1f} seconds")
        print(f"\n{'='*60}\n")

        return True

    except FileNotFoundError:
        print("❌ pg_restore not found!")
        print("   Ubuntu/Debian: sudo apt install postgresql-client")
        print("   macOS: brew install postgresql")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Cleanup temp file if we decompressed
        if temp_file and Path(temp_file.name).exists():
            Path(temp_file.name).unlink()


def main():
    parser = argparse.ArgumentParser(description="Fast database restore")
    parser.add_argument("backup", help="Backup file (.dump or .dump.gz)")
    parser.add_argument("-j", "--jobs", type=int, help=f"Parallel jobs (default: {get_cpu_count()})")
    parser.add_argument("-f", "--force", action="store_true", help="Skip confirmation")
    args = parser.parse_args()

    success = restore_database(args.backup, args.jobs, args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
