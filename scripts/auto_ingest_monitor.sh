#!/bin/bash
# Autonomous PDF ingestion with monitoring
# Logs all progress to a file for review in the morning

LOG_FILE="/home/vipul/Calculus_RAG/ingestion_log_$(date +%Y%m%d_%H%M%S).txt"
PROJECT_DIR="/home/vipul/Calculus_RAG"

cd "$PROJECT_DIR"
source .venv/bin/activate

echo "============================================================" | tee -a "$LOG_FILE"
echo "Autonomous PDF Ingestion Started: $(date)" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"

# Function to get current chunk count
get_chunk_count() {
    python3 -c "
import asyncio
import asyncpg
async def count():
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/calculus_rag')
        count = await conn.fetchval('SELECT COUNT(*) FROM calculus_knowledge')
        await conn.close()
        print(count or 0)
    except:
        print(0)
asyncio.run(count())
" 2>/dev/null
}

INITIAL_COUNT=$(get_chunk_count)
echo "Initial chunk count: $INITIAL_COUNT" | tee -a "$LOG_FILE"

# PDF 1: Calculus_1.pdf
echo "" | tee -a "$LOG_FILE"
echo ">>> [$(date '+%H:%M:%S')] Starting PDF 1/3: Calculus_1.pdf (45MB, 875 pages)" | tee -a "$LOG_FILE"
python scripts/ingest_large_pdf.py "knowledge_content/calculus/Calculus_1.pdf" --pages-per-batch 10 2>&1 | tee -a "$LOG_FILE"
COUNT_AFTER_1=$(get_chunk_count)
echo ">>> [$(date '+%H:%M:%S')] PDF 1 complete. Total chunks: $COUNT_AFTER_1" | tee -a "$LOG_FILE"

# PDF 2: Calculus_2.pdf
echo "" | tee -a "$LOG_FILE"
echo ">>> [$(date '+%H:%M:%S')] Starting PDF 2/3: Calculus_2.pdf (42MB)" | tee -a "$LOG_FILE"
python scripts/ingest_large_pdf.py "knowledge_content/calculus/Calculus_2.pdf" --pages-per-batch 10 2>&1 | tee -a "$LOG_FILE"
COUNT_AFTER_2=$(get_chunk_count)
echo ">>> [$(date '+%H:%M:%S')] PDF 2 complete. Total chunks: $COUNT_AFTER_2" | tee -a "$LOG_FILE"

# PDF 3: Calculus_Solutions.pdf
echo "" | tee -a "$LOG_FILE"
echo ">>> [$(date '+%H:%M:%S')] Starting PDF 3/3: Calculus_Solutions.pdf (16MB)" | tee -a "$LOG_FILE"
python scripts/ingest_large_pdf.py "knowledge_content/calculus/Calculus_Solutions.pdf" --pages-per-batch 10 2>&1 | tee -a "$LOG_FILE"
COUNT_AFTER_3=$(get_chunk_count)
echo ">>> [$(date '+%H:%M:%S')] PDF 3 complete. Total chunks: $COUNT_AFTER_3" | tee -a "$LOG_FILE"

# Try Khan Academy (optional - may fail if no network/API issues)
echo "" | tee -a "$LOG_FILE"
echo ">>> [$(date '+%H:%M:%S')] Attempting Khan Academy playlist ingestion..." | tee -a "$LOG_FILE"
timeout 3600 python scripts/ingest_youtube_playlist.py "https://www.youtube.com/watch?v=EKvHQc3QEow&list=PL19E79A0638C8D449" --topic calculus --batch-size 5 2>&1 | tee -a "$LOG_FILE" || echo "Khan Academy ingestion skipped or timed out" | tee -a "$LOG_FILE"

FINAL_COUNT=$(get_chunk_count)

echo "" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"
echo "INGESTION COMPLETE: $(date)" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"
echo "Initial chunks: $INITIAL_COUNT" | tee -a "$LOG_FILE"
echo "After Calculus_1: $COUNT_AFTER_1 (+$((COUNT_AFTER_1 - INITIAL_COUNT)))" | tee -a "$LOG_FILE"
echo "After Calculus_2: $COUNT_AFTER_2 (+$((COUNT_AFTER_2 - COUNT_AFTER_1)))" | tee -a "$LOG_FILE"
echo "After Solutions: $COUNT_AFTER_3 (+$((COUNT_AFTER_3 - COUNT_AFTER_2)))" | tee -a "$LOG_FILE"
echo "Final total: $FINAL_COUNT (+$((FINAL_COUNT - INITIAL_COUNT)) new chunks)" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"
echo "Log saved to: $LOG_FILE" | tee -a "$LOG_FILE"
