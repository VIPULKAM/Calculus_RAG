#!/usr/bin/env python3
"""
Fast backup of the knowledge base using pg_dump custom format + gzip.

Creates a compressed binary dump file (.dump.gz) that can be restored quickly
using parallel pg_restore.

Usage:
    python scripts/backup_db.py                    # Timestamped backup
    python scripts/backup_db.py my_backup          # Named backup
    python scripts/backup_db.py --no-gzip          # Without gzip compression

Restore:
    python scripts/restore_db.py backups/backup_2025-12-23.dump.gz
"""

import argparse
import gzip
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from calculus_rag.config import get_settings


def backup_database(backup_name: str = None, use_gzip: bool = True) -> Path:
    """
    Create a backup using pg_dump custom format.

    Custom format is compressed and supports parallel restore.

    Args:
        backup_name: Optional name for backup

    Returns:
        Path to backup file
    """
    settings = get_settings()

    # Create backups directory
    backup_dir = Path(__file__).parent.parent / "backups"
    backup_dir.mkdir(exist_ok=True)

    # Generate filename
    if backup_name:
        backup_file = backup_dir / f"{backup_name}.dump"
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = backup_dir / f"backup_{timestamp}.dump"

    print(f"\n{'='*60}")
    print(f"Database Backup (Compressed Binary)")
    print(f"{'='*60}\n")
    print(f"📦 Database: {settings.postgres_db}")
    print(f"📁 Output: {backup_file}")

    # pg_dump with custom format (compressed, supports parallel restore)
    cmd = [
        "pg_dump",
        "-h", settings.postgres_host,
        "-p", str(settings.postgres_port),
        "-U", settings.postgres_user,
        "-d", settings.postgres_db,
        "-Fc",                    # Custom format (binary, compressed)
        "-f", str(backup_file),
        "--no-owner",
        "--no-acl",
    ]

    env = {"PGPASSWORD": settings.postgres_password}

    print(f"\n⏳ Backing up (this is fast)...")
    start = datetime.now()

    try:
        result = subprocess.run(
            cmd,
            env={**os.environ, **env},
            capture_output=True,
            text=True,
        )

        elapsed = (datetime.now() - start).total_seconds()

        if result.returncode != 0:
            print(f"❌ Failed: {result.stderr}")
            return None

        dump_size_mb = backup_file.stat().st_size / 1024 / 1024

        # Compress with gzip if requested
        final_file = backup_file
        if use_gzip:
            print(f"   📦 Compressing with gzip...")
            gzip_file = Path(str(backup_file) + ".gz")
            with open(backup_file, 'rb') as f_in:
                with gzip.open(gzip_file, 'wb', compresslevel=9) as f_out:
                    shutil.copyfileobj(f_in, f_out)
            # Remove uncompressed file
            backup_file.unlink()
            final_file = gzip_file

        size_mb = final_file.stat().st_size / 1024 / 1024

        print(f"\n✅ Backup complete!")
        print(f"   📄 File: {final_file.name}")
        print(f"   📊 Size: {size_mb:.2f} MB")
        if use_gzip:
            print(f"   📉 Compression: {dump_size_mb:.2f} MB → {size_mb:.2f} MB ({100*(1-size_mb/dump_size_mb):.0f}% smaller)")
        print(f"   ⏱️  Time: {elapsed:.1f} seconds")

        # Show all backups (both .dump and .dump.gz)
        backups = sorted(
            list(backup_dir.glob("*.dump")) + list(backup_dir.glob("*.dump.gz")),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        if backups:
            print(f"\n📚 Available backups:")
            total_size = 0
            for b in backups[:5]:
                size = b.stat().st_size / 1024 / 1024
                total_size += size
                print(f"   • {b.name} ({size:.2f} MB)")
            if len(backups) > 5:
                print(f"   ... and {len(backups) - 5} more")
            print(f"   Total: {total_size:.2f} MB")

        print(f"\n{'='*60}")
        print(f"🔄 To restore: python scripts/restore_db.py {final_file.name}")
        print(f"{'='*60}\n")

        return final_file

    except FileNotFoundError:
        print("❌ pg_dump not found!")
        print("   Ubuntu/Debian: sudo apt install postgresql-client")
        print("   macOS: brew install postgresql")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Database backup (compressed binary format)")
    parser.add_argument("name", nargs="?", help="Backup name (optional)")
    parser.add_argument("--no-gzip", action="store_true", help="Skip gzip compression")
    args = parser.parse_args()

    backup_file = backup_database(args.name, use_gzip=not args.no_gzip)
    sys.exit(0 if backup_file else 1)


if __name__ == "__main__":
    main()
