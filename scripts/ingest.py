#!/usr/bin/env python3
"""Main orchestration entrypoint for video-research-ingest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from download import acquire_source
from analysis import analyze_transcript
from export_obsidian import export_note_to_obsidian
from frames import extract_representative_frames
from markdown import build_note
from transcript import build_transcript
from utils import (
    ensure_dir,
    get_output_dir,
    probe_media,
    seconds_to_hhmmss,
    slugify,
    utc_today,
    utc_timestamp_slug,
    write_json,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Video URL or local file path")
    parser.add_argument("--export-obsidian", action="store_true")
    parser.add_argument("--template", default="default-video-note.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_root = ensure_dir(get_output_dir())
    run_dir = ensure_dir(output_root / f"{utc_timestamp_slug()}-{slugify(args.input)[:50]}")
    frames_dir = ensure_dir(run_dir / "frames")

    source = acquire_source(args.input, run_dir)
    media = probe_media(source["video_path"])
    frames = extract_representative_frames(source["video_path"], frames_dir)
    transcript = build_transcript(source["video_path"], source.get("subtitle_path"), run_dir)

    raw_download_metadata = source.get("download_metadata", {}) or {}
    raw_download_metadata_path = None
    curated_download_metadata = {}
    if raw_download_metadata:
        raw_download_metadata_path = run_dir / "download-info.json"
        write_json(raw_download_metadata_path, raw_download_metadata)
        curated_download_metadata = {
            "id": raw_download_metadata.get("id"),
            "webpage_url": raw_download_metadata.get("webpage_url") or source["source_url"],
            "description": raw_download_metadata.get("description", "")[:500],
            "upload_date": raw_download_metadata.get("upload_date"),
            "timestamp": raw_download_metadata.get("timestamp"),
            "view_count": raw_download_metadata.get("view_count"),
            "like_count": raw_download_metadata.get("like_count"),
            "channel_id": raw_download_metadata.get("channel_id"),
            "uploader_id": raw_download_metadata.get("uploader_id"),
            "categories": raw_download_metadata.get("categories") or [],
            "tags": (raw_download_metadata.get("tags") or [])[:15],
        }

    metadata_json = {
        "title": source["title"],
        "source_url": source["source_url"],
        "source_file": source["source_file"],
        "video_platform": source["video_platform"],
        "channel_or_author": source["channel_or_author"],
        "date_ingested": utc_today(),
        "duration_seconds": media["duration_seconds"],
        "duration": seconds_to_hhmmss(media["duration_seconds"]),
        "size_bytes": media["size_bytes"],
        "format_name": media["format_name"],
        "frames": frames,
        "transcript_source": transcript["transcript_source"],
        "subtitle_file": source.get("subtitle_path").name if source.get("subtitle_path") else None,
        "download_metadata": curated_download_metadata,
        "download_metadata_path": str(raw_download_metadata_path) if raw_download_metadata_path else None,
        "classification": {
            "type": "inspiration",
            "confidence": "pending-review",
        },
    }

    frame_index = "\n".join(f"- `{item['relative_path']}` — {item['label']}" for item in frames) or "- No frames extracted"

    transcript_vtt_path = run_dir / "transcript.vtt"
    analysis = analyze_transcript(
        title=source["title"],
        transcript_text=transcript["transcript_text"],
        transcript_vtt_path=transcript_vtt_path if transcript_vtt_path.exists() else None,
        metadata=metadata_json,
    )

    metadata_json["classification"] = analysis["classification"]
    metadata_json["analysis_keywords"] = analysis["keywords"]

    source_metadata_block = "```json\n" + json.dumps(metadata_json, indent=2, ensure_ascii=False) + "\n```"

    context = {
        "title": source["title"],
        "source_url": source["source_url"],
        "source_file": source["source_file"],
        "video_platform": source["video_platform"],
        "date_ingested": utc_today(),
        "duration": seconds_to_hhmmss(media["duration_seconds"]),
        "channel_or_author": source["channel_or_author"],
        "transcript_text": transcript["transcript_text"],
        "frame_index": frame_index,
        "source_metadata_block": source_metadata_block,
        "metadata_json": metadata_json,
        "template_name": args.template,
        "classification_type": metadata_json["classification"]["type"],
        "classification_confidence": metadata_json["classification"]["confidence"],
        "classification_block": analysis["classification_block"],
        "executive_summary": analysis["executive_summary"],
        "key_insights": analysis["key_insights"],
        "timestamped_notes": analysis["timestamped_notes"],
        "reviewer_feedback": analysis["reviewer_feedback"],
        "suggested_followups": analysis["suggested_followups"],
    }

    note_path = build_note(run_dir, context)
    print(f"note_path={note_path}")
    print(f"metadata_path={run_dir / 'metadata.json'}")
    print(f"frames_dir={frames_dir}")
    print(f"transcript_path={transcript['transcript_path']}")

    if args.export_obsidian:
        exported = export_note_to_obsidian(note_path)
        print(f"obsidian_export={exported}")


if __name__ == "__main__":
    main()
