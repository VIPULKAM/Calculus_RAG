#!/usr/bin/env python3
"""
Retry downloading transcripts for videos that failed previously.
Uses yt-dlp for subtitle extraction which is more reliable.
"""

import asyncio
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.llm.ollama_llm import OllamaLLM
from calculus_rag.llm.base import LLMMessage


# Videos that failed to get transcripts
FAILED_VIDEOS = [
    {"video_id": "W0VWO4asgmk", "title": "Introduction to limits 2 | Limits | Precalculus | Khan Academy"},
    {"video_id": "GGQngIp0YGI", "title": "Limit examples (part 1) | Limits | Differential Calculus | Khan Academy"},
    {"video_id": "xjkSE9cPqzo", "title": "Limit examples w/ brain malfunction on first prob (part 4) | Differential Calculus | Khan Academy"},
    {"video_id": "Ve99biD1KtA", "title": "Proof: lim (sin x)/x | Limits | Differential Calculus | Khan Academy"},
    {"video_id": "U_8GRLJplZg", "title": "Sequences and series (part 2)"},
]


def get_transcript_ytdlp(video_id: str) -> str | None:
    """Fetch transcript using yt-dlp subtitle download."""
    url = f"https://www.youtube.com/watch?v={video_id}"

    with tempfile.TemporaryDirectory() as tmpdir:
        output_template = f"{tmpdir}/%(id)s.%(ext)s"

        try:
            # Download auto-generated English subtitles using browser cookies
            result = subprocess.run(
                [
                    "yt-dlp",
                    "--cookies-from-browser", "firefox",
                    "--skip-download",
                    "--write-auto-sub",
                    "--sub-lang", "en",
                    "-o", output_template,
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Find the subtitle file (VTT or SRT)
            sub_file = None
            for ext in ["vtt", "srt"]:
                candidate = Path(tmpdir) / f"{video_id}.en.{ext}"
                if candidate.exists():
                    sub_file = candidate
                    break

            # Try finding any subtitle file
            if not sub_file:
                for f in Path(tmpdir).glob("*.vtt"):
                    sub_file = f
                    break
            if not sub_file:
                for f in Path(tmpdir).glob("*.srt"):
                    sub_file = f
                    break

            if not sub_file or not sub_file.exists():
                print(f"  ⚠️  No subtitle file created")
                print(f"  Debug: Files in tmpdir: {list(Path(tmpdir).glob('*'))}")
                return None

            # Parse subtitle file and extract text
            content = sub_file.read_text(encoding="utf-8")

            # Remove VTT/SRT formatting (timestamps, sequence numbers, headers)
            lines = []
            for line in content.split("\n"):
                line = line.strip()
                # Skip empty lines, sequence numbers, and timestamps
                if not line:
                    continue
                if line.isdigit():
                    continue
                if "-->" in line:
                    continue
                # Skip VTT header
                if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
                    continue
                # Clean up HTML-like tags and VTT formatting
                line = re.sub(r'<[^>]+>', '', line)
                line = re.sub(r'&nbsp;', ' ', line)
                if line:
                    lines.append(line)

            # Join and remove duplicate consecutive lines (common in auto-subs)
            text_parts = []
            prev_line = ""
            for line in lines:
                if line != prev_line:
                    text_parts.append(line)
                    prev_line = line

            return " ".join(text_parts)

        except subprocess.TimeoutExpired:
            print(f"  ⚠️  Timeout downloading subtitles")
            return None
        except Exception as e:
            print(f"  ❌ Error: {e}")
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

    messages = [LLMMessage(role="user", content=prompt)]

    try:
        response = llm.generate(messages, temperature=0.3)
        return response.content
    except Exception as e:
        print(f"  ❌ LLM error: {e}")
        return None


def create_markdown_file(output_dir: Path, video_info: dict, summary: str) -> Path:
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
topic: precalculus.khan_academy
title: "{video_info['title']}"
source: Khan Academy
source_url: https://www.youtube.com/watch?v={video_info['video_id']}
video_id: {video_info['video_id']}
difficulty: {difficulty}
content_type: video_summary
---

# {video_info['title']}

*Source: [Khan Academy Video](https://www.youtube.com/watch?v={video_info['video_id']})*

"""

    content = frontmatter + summary
    output_path = output_dir / filename
    output_path.write_text(content, encoding="utf-8")
    return output_path


async def main():
    """Retry failed videos."""
    print("=" * 70)
    print("RETRYING FAILED TRANSCRIPTS (using yt-dlp)")
    print("=" * 70)

    output_dir = Path(__file__).parent.parent / "knowledge_content" / "khan_academy" / "precalculus"

    # Initialize LLM
    settings = get_settings()
    llm = OllamaLLM(
        model="qwen2-math:7b",
        base_url=settings.ollama_base_url,
        timeout=120,
    )
    print(f"🤖 LLM: {llm.model_name}")

    successful = 0
    failed = 0

    for i, video_info in enumerate(FAILED_VIDEOS, 1):
        print(f"\n[{i}/{len(FAILED_VIDEOS)}] {video_info['title'][:50]}...")

        # Get transcript using yt-dlp
        print(f"  📥 Fetching subtitles for {video_info['video_id']}...")
        transcript = get_transcript_ytdlp(video_info["video_id"])

        if not transcript:
            print(f"  ❌ Could not get transcript")
            failed += 1
            continue

        print(f"  📝 Transcript: {len(transcript)} chars")

        # Summarize
        print(f"  🤖 Summarizing...")
        summary = summarize_transcript(llm, video_info["title"], transcript)

        if not summary:
            print(f"  ❌ Summarization failed")
            failed += 1
            continue

        # Save
        md_path = create_markdown_file(output_dir, video_info, summary)
        print(f"  ✅ Saved: {md_path.name}")
        successful += 1

        time.sleep(3)

    print("\n" + "=" * 70)
    print("RETRY COMPLETE")
    print("=" * 70)
    print(f"✅ Successful: {successful}/{len(FAILED_VIDEOS)}")
    print(f"❌ Failed: {failed}/{len(FAILED_VIDEOS)}")


if __name__ == "__main__":
    asyncio.run(main())
