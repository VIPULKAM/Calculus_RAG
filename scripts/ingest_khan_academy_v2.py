#!/usr/bin/env python3
"""
Ingest Khan Academy YouTube playlist using yt-dlp for subtitles.

Uses yt-dlp instead of youtube-transcript-api for better rate limit handling.
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.llm.ollama_llm import OllamaLLM


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


def get_subtitle_with_ytdlp(video_id: str, temp_dir: str, use_tor: bool = True) -> str | None:
    """Fetch subtitles using yt-dlp via Tor for IP rotation."""
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    output_template = os.path.join(temp_dir, f"{video_id}")

    # Use torsocks to route through Tor
    cmd_prefix = ["torsocks"] if use_tor else []

    try:
        # Try to get auto-generated subtitles
        result = subprocess.run(
            cmd_prefix + [
                "yt-dlp",
                "--skip-download",
                "--write-auto-sub",
                "--sub-lang", "en",
                "--sub-format", "vtt",
                "--output", output_template,
                "--no-warnings",
                "--quiet",
                video_url,
            ],
            capture_output=True,
            text=True,
            timeout=90,  # Longer timeout for Tor
        )

        # Look for the subtitle file
        vtt_file = f"{output_template}.en.vtt"
        if os.path.exists(vtt_file):
            with open(vtt_file, "r") as f:
                vtt_content = f.read()
            os.remove(vtt_file)
            return parse_vtt(vtt_content)

        # Try manual subs if auto-subs not available
        result = subprocess.run(
            cmd_prefix + [
                "yt-dlp",
                "--skip-download",
                "--write-sub",
                "--sub-lang", "en",
                "--sub-format", "vtt",
                "--output", output_template,
                "--no-warnings",
                "--quiet",
                video_url,
            ],
            capture_output=True,
            text=True,
            timeout=90,
        )

        if os.path.exists(vtt_file):
            with open(vtt_file, "r") as f:
                vtt_content = f.read()
            os.remove(vtt_file)
            return parse_vtt(vtt_content)

        return None

    except subprocess.TimeoutExpired:
        print(f"  ⚠️  Timeout fetching subtitles")
        return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None


def parse_vtt(vtt_content: str) -> str:
    """Parse VTT subtitle file and extract plain text."""
    lines = vtt_content.split("\n")
    text_lines = []

    for line in lines:
        line = line.strip()
        # Skip headers, timestamps, and empty lines
        if not line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if re.match(r"^\d{2}:\d{2}", line) or re.match(r"^NOTE", line):
            continue
        if "-->" in line:
            continue
        # Remove VTT formatting tags
        line = re.sub(r"<[^>]+>", "", line)
        if line:
            text_lines.append(line)

    # Remove consecutive duplicates (VTT often repeats lines)
    deduped = []
    for line in text_lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)

    return " ".join(deduped)


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
    print("KHAN ACADEMY INGESTION (via Tor)")
    print("=" * 70)
    print("🧅 Using Tor for anonymous fetching...")

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

    # Create temp dir for subtitles
    with tempfile.TemporaryDirectory() as temp_dir:
        successful = 0
        failed = 0
        skipped = 0

        print(f"\n🚀 Processing videos...\n")

        for i, video_info in enumerate(videos, 1):
            print(f"[{i}/{total_videos}] {video_info['title'][:50]}...")

            # Check if already processed
            safe_title = re.sub(r'[^\w\s-]', '', video_info["title"])
            safe_title = re.sub(r'\s+', '_', safe_title).strip('_')[:50]
            existing_file = output_dir / f"{safe_title}.md"
            if existing_file.exists():
                # Check if it has substantial content (not just stub)
                content = existing_file.read_text()
                if len(content) > 1000:  # Good summary
                    print(f"  ⏭️  Already exists (good quality), skipping")
                    skipped += 1
                    successful += 1
                    continue
                else:
                    print(f"  🔄 Exists but low quality, regenerating...")

            # Get transcript using yt-dlp
            transcript = get_subtitle_with_ytdlp(video_info["video_id"], temp_dir)
            if not transcript:
                print(f"  ⚠️  No subtitles available")
                failed += 1
                # Rate limit even on failure
                time.sleep(5)
                continue

            print(f"  📝 Transcript: {len(transcript)} chars")

            # Summarize
            print(f"  🤖 Summarizing...")
            summary = summarize_transcript(llm, video_info["title"], transcript)
            if not summary:
                failed += 1
                continue

            # Save
            md_path = create_markdown_file(output_dir, video_info, summary, topic_category)
            print(f"  ✅ Saved: {md_path.name}")

            successful += 1

            # Rate limiting
            time.sleep(5)  # 5 seconds between videos

            if successful % 5 == 0:
                print(f"\n  ⏸️  Batch pause... waiting 30s")
                time.sleep(30)

    # Summary
    print("\n" + "=" * 70)
    print("INGESTION COMPLETE")
    print("=" * 70)
    print(f"✅ Successful: {successful}/{total_videos}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"❌ Failed: {failed}/{total_videos}")
    print(f"📁 Files: {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
