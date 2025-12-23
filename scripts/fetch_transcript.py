#!/usr/bin/env python3
"""Standalone script to fetch a single transcript. Run with torsocks."""
import sys
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

def main():
    if len(sys.argv) < 2:
        print("ERROR: No video ID provided", file=sys.stderr)
        sys.exit(1)

    video_id = sys.argv[1]

    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        text = " ".join([s.text.replace("\n", " ") for s in transcript.snippets])
        print(text)
        sys.exit(0)
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        print(f"NO_TRANSCRIPT: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
