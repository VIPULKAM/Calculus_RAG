#!/bin/bash
# Ingest all 3 large PDFs sequentially
# This script can be interrupted and resumed - progress is tracked per PDF

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"
source .venv/bin/activate

echo "============================================================"
echo "Large PDF Ingestion - All 3 PDFs"
echo "Started: $(date)"
echo "============================================================"

# PDF 1: Calculus_1.pdf (45MB, 875 pages)
echo ""
echo ">>> PDF 1/3: Calculus_1.pdf"
python scripts/ingest_large_pdf.py "knowledge_content/calculus/Calculus_1.pdf" --pages-per-batch 10

# PDF 2: Calculus_2.pdf (42MB)
echo ""
echo ">>> PDF 2/3: Calculus_2.pdf"
python scripts/ingest_large_pdf.py "knowledge_content/calculus/Calculus_2.pdf" --pages-per-batch 10

# PDF 3: Calculus_Solutions.pdf (16MB)
echo ""
echo ">>> PDF 3/3: Calculus_Solutions.pdf"
python scripts/ingest_large_pdf.py "knowledge_content/calculus/Calculus_Solutions.pdf" --pages-per-batch 10

echo ""
echo "============================================================"
echo "All PDFs ingested successfully!"
echo "Completed: $(date)"
echo "============================================================"

# Show final database count
python -c "
import asyncio
import asyncpg

async def count():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/calculus_rag')
    count = await conn.fetchval('SELECT COUNT(*) FROM calculus_knowledge')
    await conn.close()
    print(f'Total chunks in database: {count}')

asyncio.run(count())
"
