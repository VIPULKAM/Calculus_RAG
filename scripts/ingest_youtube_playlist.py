#!/usr/bin/env python3
"""
Khan Academy YouTube Playlist Ingestion.

Fetches videos from a YouTube playlist, extracts transcripts/descriptions,
generates educational summaries using LLM, and ingests into vector database.

Usage:
    python scripts/ingest_youtube_playlist.py <playlist_url> [--topic calculus] [--batch-size 5]
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.embeddings.ollama_embedder import OllamaEmbedder
from calculus_rag.llm.ollama_llm import OllamaLLM
from calculus_rag.vectorstore.pgvector_store import PgVectorStore

# Output directory for markdown files
KHAN_ACADEMY_DIR = Path(__file__).parent.parent / "knowledge_content" / "khan_academy"
PROGRESS_FILE = Path(__file__).parent.parent / ".youtube_progress.json"


def load_progress() -> dict:
    """Load ingestion progress from file."""
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {}


def save_progress(progress: dict):
    """Save ingestion progress to file."""
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


def sanitize_filename(title: str) -> str:
    """Convert title to valid filename."""
    # Remove special characters, keep alphanumeric and spaces
    clean = re.sub(r'[^\w\s-]', '', title)
    # Replace spaces with underscores
    clean = re.sub(r'\s+', '_', clean)
    # Truncate to reasonable length
    return clean[:60]


def get_playlist_videos(playlist_url: str) -> list[dict]:
    """Fetch video metadata from YouTube playlist using yt-dlp."""
    print(f"Fetching playlist info from: {playlist_url}")

    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        playlist_url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error fetching playlist: {result.stderr}")
        return []

    videos = []
    for line in result.stdout.strip().split('\n'):
        if line:
            try:
                video = json.loads(line)
                videos.append({
                    "id": video.get("id"),
                    "title": video.get("title", "Untitled"),
                    "url": video.get("url") or f"https://www.youtube.com/watch?v={video.get('id')}",
                    "duration": video.get("duration"),
                })
            except json.JSONDecodeError:
                continue

    print(f"Found {len(videos)} videos in playlist")
    return videos


def get_video_transcript(video_id: str) -> str | None:
    """Fetch auto-generated subtitles/transcript for a video."""
    cmd = [
        "yt-dlp",
        "--write-auto-sub",
        "--sub-lang", "en",
        "--skip-download",
        "--output", "/tmp/%(id)s",
        f"https://www.youtube.com/watch?v={video_id}",
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Look for subtitle file
        sub_files = [
            f"/tmp/{video_id}.en.vtt",
            f"/tmp/{video_id}.en.srt",
        ]

        for sub_file in sub_files:
            if os.path.exists(sub_file):
                content = Path(sub_file).read_text()
                # Clean up VTT/SRT format
                lines = []
                for line in content.split('\n'):
                    # Skip timing lines and headers
                    if '-->' in line or line.strip().isdigit() or 'WEBVTT' in line:
                        continue
                    if line.strip():
                        # Remove HTML tags
                        clean = re.sub(r'<[^>]+>', '', line)
                        lines.append(clean)

                os.remove(sub_file)
                return ' '.join(lines)

        return None
    except Exception as e:
        print(f"    Warning: Could not fetch transcript: {e}")
        return None


def get_video_description(video_id: str) -> str:
    """Fetch video description."""
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--get-description",
        f"https://www.youtube.com/watch?v={video_id}",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def generate_summary(
    llm: OllamaLLM,
    title: str,
    transcript: str | None,
    description: str,
) -> dict:
    """Generate structured educational summary using LLM."""

    context = f"Title: {title}\n\n"
    if transcript:
        # Truncate long transcripts
        context += f"Transcript:\n{transcript[:8000]}\n\n"
    if description:
        context += f"Description:\n{description[:2000]}\n\n"

    prompt = f"""You are an expert math educator. Create a structured educational summary of this Khan Academy video about calculus.

{context}

Create a summary in this exact format:

## Key Concepts
- (list 3-5 main concepts covered, as bullet points)

## Definitions
- **Term**: Definition with formula if applicable (use LaTeX like $f'(x)$)

## Examples & Steps
### Example: (brief title)
**Step 1:** Description
**Step 2:** Description
(include any formulas)

## Summary
(2-3 sentence summary of the main takeaways)

Be concise but accurate. Use proper LaTeX notation for all math formulas."""

    try:
        from calculus_rag.llm.base import LLMMessage
        response = llm.generate([
            LLMMessage(role="user", content=prompt)
        ], temperature=0.3)
        return {"success": True, "content": response.content}
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_markdown_file(
    video: dict,
    summary_content: str,
    topic: str,
    output_dir: Path,
) -> Path:
    """Create markdown file for video summary."""
    filename = sanitize_filename(video["title"]) + ".md"
    filepath = output_dir / filename

    frontmatter = f"""---
topic: {topic}.khan_academy
title: "{video['title']}"
source: Khan Academy
source_url: {video['url']}
video_id: {video['id']}
difficulty: 2
content_type: video_summary
---

# {video['title']}

*Source: [Khan Academy Video]({video['url']})*

{summary_content}
"""

    filepath.write_text(frontmatter)
    return filepath


async def ingest_markdown(
    vector_store: PgVectorStore,
    embedder: OllamaEmbedder,
    filepath: Path,
    video: dict,
    topic: str,
) -> int:
    """Ingest markdown file into vector store."""
    content = filepath.read_text()

    # Split into chunks (skip frontmatter)
    parts = content.split("---", 2)
    if len(parts) >= 3:
        body = parts[2].strip()
    else:
        body = content

    # Split by sections
    sections = re.split(r'\n## ', body)
    chunks = []

    for section in sections:
        if section.strip():
            # Include section header
            section_text = "## " + section if not section.startswith("#") else section
            # Split large sections
            if len(section_text) > 600:
                # Split by paragraphs
                paragraphs = section_text.split('\n\n')
                current_chunk = ""
                for para in paragraphs:
                    if len(current_chunk) + len(para) < 600:
                        current_chunk += para + "\n\n"
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = para + "\n\n"
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
            else:
                chunks.append(section_text.strip())

    if not chunks:
        return 0

    # Prepare batch data
    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        try:
            embedding = embedder.embed(chunk)

            chunk_id = f"khan_{video['id']}_{i}"
            metadata = {
                "source": f"Khan Academy: {video['title']}",
                "source_url": video["url"],
                "video_id": video["id"],
                "chunk_index": i,
                "category": "Khan Academy",
                "topic": topic,
                "content_type": "video_summary",
            }

            ids.append(chunk_id)
            embeddings.append(embedding)
            documents.append(chunk)
            metadatas.append(metadata)

        except Exception as e:
            print(f"    Warning: Failed to embed chunk: {e}")

    if ids:
        await vector_store.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        return len(ids)

    return 0


async def process_video(
    video: dict,
    llm: OllamaLLM,
    embedder: OllamaEmbedder,
    vector_store: PgVectorStore,
    topic: str,
    output_dir: Path,
) -> tuple[bool, int]:
    """Process a single video: fetch, summarize, save, ingest."""
    video_id = video["id"]

    # Get transcript and description
    print(f"    Fetching content...", end=" ", flush=True)
    transcript = get_video_transcript(video_id)
    description = get_video_description(video_id)

    if not transcript and not description:
        print("No content available, skipping")
        return False, 0

    print(f"{'transcript' if transcript else 'description only'}")

    # Generate summary
    print(f"    Generating summary...", end=" ", flush=True)
    result = generate_summary(llm, video["title"], transcript, description)

    if not result["success"]:
        print(f"Failed: {result['error']}")
        return False, 0

    print("Done")

    # Create markdown file
    print(f"    Saving markdown...", end=" ", flush=True)
    filepath = create_markdown_file(video, result["content"], topic, output_dir)
    print(f"Saved to {filepath.name}")

    # Ingest into vector store
    print(f"    Ingesting...", end=" ", flush=True)
    chunks = await ingest_markdown(vector_store, embedder, filepath, video, topic)
    print(f"{chunks} chunks")

    return True, chunks


async def main():
    parser = argparse.ArgumentParser(description="Ingest YouTube playlist into knowledge base")
    parser.add_argument("playlist_url", help="YouTube playlist URL")
    parser.add_argument("--topic", default="calculus", help="Topic category (default: calculus)")
    parser.add_argument("--batch-size", type=int, default=5, help="Videos to process per batch")
    parser.add_argument("--start-index", type=int, default=None, help="Start from specific video index")
    parser.add_argument("--reset", action="store_true", help="Reset progress and start fresh")
    args = parser.parse_args()

    # Create output directory
    output_dir = KHAN_ACADEMY_DIR / args.topic
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load progress
    progress = load_progress()
    playlist_key = args.playlist_url.split("list=")[-1][:20]

    if args.reset and playlist_key in progress:
        del progress[playlist_key]
        save_progress(progress)
        print(f"Reset progress for playlist")

    print(f"\n{'='*60}")
    print(f"Khan Academy Playlist Ingestion")
    print(f"{'='*60}")
    print(f"Topic: {args.topic}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")

    # Fetch playlist
    videos = get_playlist_videos(args.playlist_url)
    if not videos:
        print("No videos found in playlist")
        return

    # Determine starting point
    if args.start_index is not None:
        start_idx = args.start_index
    elif playlist_key in progress:
        start_idx = progress[playlist_key].get("last_index", 0)
        print(f"Resuming from video {start_idx + 1}")
    else:
        start_idx = 0

    # Initialize components
    settings = get_settings()

    print("\nInitializing components...")
    embedder = OllamaEmbedder(
        model=settings.embedding_model_name,
        base_url=settings.ollama_base_url,
        dimension=settings.vector_dimension,
    )

    # Use the larger model for better summaries
    llm = OllamaLLM(
        model="qwen2-math:7b",
        base_url=settings.ollama_base_url,
        timeout=300,
    )

    vector_store = PgVectorStore(
        connection_string=settings.postgres_dsn,
        dimension=settings.vector_dimension,
        table_name="calculus_knowledge",
    )
    await vector_store.initialize()

    print(f"\nProcessing {len(videos) - start_idx} remaining videos...\n")

    total_chunks = 0
    processed = 0

    try:
        for idx, video in enumerate(videos[start_idx:], start=start_idx):
            print(f"\n[{idx + 1}/{len(videos)}] {video['title']}")

            start_time = time.time()
            success, chunks = await process_video(
                video, llm, embedder, vector_store, args.topic, output_dir
            )
            elapsed = time.time() - start_time

            if success:
                processed += 1
                total_chunks += chunks
                print(f"    Completed in {elapsed:.1f}s")

            # Save progress
            progress[playlist_key] = {
                "last_index": idx + 1,
                "total_videos": len(videos),
                "processed": progress.get(playlist_key, {}).get("processed", 0) + (1 if success else 0),
                "chunks_ingested": progress.get(playlist_key, {}).get("chunks_ingested", 0) + chunks,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            save_progress(progress)

            # Brief pause between videos
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print(f"\n\nInterrupted! Progress saved at video {idx + 1}")

    finally:
        await vector_store.close()

    print(f"\n{'='*60}")
    print(f"Ingestion Complete!")
    print(f"{'='*60}")
    print(f"Videos processed this session: {processed}")
    print(f"Chunks ingested this session: {total_chunks}")
    print(f"Total progress: {progress.get(playlist_key, {})}")
    print(f"\nEmbedding cache stats: {embedder.cache_stats}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
