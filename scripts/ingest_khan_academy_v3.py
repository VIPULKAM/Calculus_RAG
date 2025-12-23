#!/usr/bin/env python3
"""
Ingest Khan Academy YouTube playlist using youtube-transcript-api with Tor proxy.
"""

import asyncio
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.llm.ollama_llm import OllamaLLM

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound


def set_tor_proxy():
    """Enable Tor proxy for subsequent requests."""
    import os
    os.environ['HTTP_PROXY'] = 'socks5h://127.0.0.1:9050'
    os.environ['HTTPS_PROXY'] = 'socks5h://127.0.0.1:9050'


def clear_tor_proxy():
    """Disable Tor proxy."""
    import os
    os.environ.pop('HTTP_PROXY', None)
    os.environ.pop('HTTPS_PROXY', None)


def get_playlist_videos(playlist_url: str) -> list[dict]:
    """Get all video info from playlist using yt-dlp."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--dump-json", playlist_url],
            capture_output=True,
            text=True,
            timeout=120,
        )

        videos = []
        for line in result.stdout.strip().split("\n"):
            if line:
                data = json.loads(line)
                videos.append({
                    "video_id": data.get("id"),
                    "title": data.get("title", "Unknown"),
                    "url": f"https://www.youtube.com/watch?v={data.get('id')}",
                })
        return videos
    except Exception as e:
        print(f"❌ Error getting playlist: {e}")
        return []


def get_video_transcript(video_id: str, use_tor: bool = True) -> str | None:
    """Fetch transcript using youtube-transcript-api with Tor proxy."""
    try:
        # Add delay before request
        time.sleep(2)

        # Using VPN - no proxy needed
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)

        # Combine all text segments from snippets
        full_text = " ".join([snippet.text.replace("\n", " ") for snippet in transcript.snippets])
        return full_text
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        print(f"  ⚠️  No transcript: {str(e)[:50]}")
        return None
    except Exception as e:
        error_msg = str(e)
        if "blocking" in error_msg.lower() or "ip" in error_msg.lower():
            print(f"  ⚠️  IP blocked, waiting 30s...")
            time.sleep(30)
        print(f"  ❌ Error: {error_msg[:80]}")
        return None


def summarize_transcript(llm: OllamaLLM, title: str, transcript: str) -> str:
    """Use LLM to create structured notes from transcript."""

    max_chars = 8000
    if len(transcript) > max_chars:
        transcript = transcript[:max_chars] + "... [truncated]"

    prompt = f"""You are creating study notes from a Khan Academy video transcript.

Video Title: {title}

Transcript:
{transcript}

Create clear, structured study notes following this format:

## Key Concepts
- List the main mathematical concepts covered
- Use clear, simple language

## Definitions
- Define any important terms introduced
- Use mathematical notation where appropriate (LaTeX: $...$)

## Examples & Steps
- Include any worked examples from the video
- Show step-by-step solutions if applicable

## Summary
- 2-3 sentence summary of what was taught

Important:
- Focus on mathematical accuracy
- Use LaTeX notation for equations (e.g., $x^2$, $\\frac{{a}}{{b}}$)
- Keep explanations clear for high school students
- Extract the educational content, ignore filler words

Create the notes now:"""

    from calculus_rag.llm.base import LLMMessage

    messages = [LLMMessage(role="user", content=prompt)]

    try:
        response = llm.generate(messages, temperature=0.3)
        return response.content
    except Exception as e:
        print(f"  ❌ LLM error: {e}")
        return None


def create_markdown_file(
    output_dir: Path,
    video_info: dict,
    summary: str,
    topic_category: str = "precalculus",
) -> Path:
    """Create a markdown file with frontmatter."""

    safe_title = re.sub(r'[^\w\s-]', '', video_info["title"])
    safe_title = re.sub(r'\s+', '_', safe_title).strip('_')[:50]
    filename = f"{safe_title}.md"

    title_lower = video_info["title"].lower()
    if any(word in title_lower for word in ["intro", "basic", "what is"]):
        difficulty = 1
    elif any(word in title_lower for word in ["advanced", "complex", "proof"]):
        difficulty = 4
    else:
        difficulty = 2

    frontmatter = f"""---
topic: {topic_category}.khan_academy
title: "{video_info['title']}"
source: Khan Academy
source_url: {video_info['url']}
video_id: {video_info['video_id']}
difficulty: {difficulty}
content_type: video_summary
---

# {video_info['title']}

*Source: [Khan Academy Video]({video_info['url']})*

"""

    content = frontmatter + summary
    output_path = output_dir / filename
    output_path.write_text(content, encoding="utf-8")

    return output_path


async def main():
    """Main ingestion pipeline."""

    playlist_url = "https://www.youtube.com/watch?v=riXcZT2ICjA&list=PLE88E3C9C7791BD2D"
    topic_category = "precalculus"

    print("=" * 70)
    print("KHAN ACADEMY INGESTION (via VPN)")
    print("=" * 70)
    print("🔒 Using VPN connection...")

    output_dir = Path(__file__).parent.parent / "knowledge_content" / "khan_academy" / topic_category
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Output directory: {output_dir}")

    # Initialize LLM
    settings = get_settings()
    if settings.cloud_llm_enabled:
        llm = OllamaLLM(
            model=settings.cloud_llm_model,
            base_url=settings.ollama_base_url,
            timeout=settings.cloud_llm_timeout,
        )
        print(f"🤖 LLM: {llm.model_name} (Cloud)")
    else:
        llm = OllamaLLM(
            model="qwen2-math:1.5b",
            base_url=settings.ollama_base_url,
            timeout=120,
        )
        print(f"🤖 LLM: {llm.model_name} (Local)")

    # Get playlist
    print(f"\n📺 Fetching playlist...")
    videos = get_playlist_videos(playlist_url)
    total_videos = len(videos)

    if total_videos == 0:
        print("❌ No videos found")
        return

    print(f"   Found {total_videos} videos")

    # Process each video
    successful = 0
    failed = 0
    skipped = 0
    new_files = 0

    print(f"\n🚀 Processing videos...\n")

    for i, video_info in enumerate(videos, 1):
        print(f"[{i}/{total_videos}] {video_info['title'][:50]}...", flush=True)

        # Check if already processed
        safe_title = re.sub(r'[^\w\s-]', '', video_info["title"])
        safe_title = re.sub(r'\s+', '_', safe_title).strip('_')[:50]
        existing_file = output_dir / f"{safe_title}.md"
        if existing_file.exists():
            content = existing_file.read_text()
            if len(content) > 1000:
                print(f"  ⏭️  Already done (good quality)", flush=True)
                skipped += 1
                successful += 1
                continue

        # Get transcript
        transcript = get_video_transcript(video_info["video_id"])
        if not transcript:
            failed += 1
            time.sleep(5)  # Extra delay on failure
            continue

        print(f"  📝 Transcript: {len(transcript)} chars", flush=True)

        # Summarize
        print(f"  🤖 Summarizing...", flush=True)
        summary = summarize_transcript(llm, video_info["title"], transcript)
        if not summary:
            failed += 1
            continue

        # Save
        md_path = create_markdown_file(output_dir, video_info, summary, topic_category)
        print(f"  ✅ Saved: {md_path.name}", flush=True)

        successful += 1
        new_files += 1

        # Rate limiting
        time.sleep(5)

        if new_files % 3 == 0:
            print(f"\n  ⏸️  Batch pause ({new_files} new)... waiting 30s\n", flush=True)
            time.sleep(30)

    # Summary
    print("\n" + "=" * 70)
    print("INGESTION COMPLETE")
    print("=" * 70)
    print(f"✅ Successful: {successful}/{total_videos}")
    print(f"🆕 New files: {new_files}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"❌ Failed: {failed}/{total_videos}")
    print(f"📁 Files: {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
