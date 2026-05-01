#!/usr/bin/env python3
"""Batch-ingest multiple video sources and optionally export notes to local-library."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from utils import ROOT_DIR, ensure_dir, slugify


LOCAL_LIBRARY_NOTES_DIR = ROOT_DIR / "local-library" / "notes"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", required=True, help="Text file containing one local path or URL per line")
    parser.add_argument("--batch-name", required=True, help="Folder name to create under local-library/notes")
    parser.add_argument(
        "--skip-local-library-copy",
        action="store_true",
        help="Leave artifacts only in output/ and do not copy note + metadata into local-library/notes/<batch-name>/",
    )
    return parser.parse_args()


def parse_source_list(path: Path) -> list[str]:
    sources: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        sources.append(stripped)
    return sources


def slugged_note_stem(index: int, title: str) -> str:
    return f"{index:02d}-{slugify(title)[:80]}"


def parse_ingest_output(stdout: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in {"note_path", "metadata_path", "frames_dir", "transcript_path", "obsidian_export"}:
            result[key] = value.strip()
    return result


def run_ingest(source: str) -> dict[str, str]:
    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "ingest.py"), "--input", source],
        text=True,
        capture_output=True,
        check=True,
        cwd=str(ROOT_DIR),
    )
    parsed = parse_ingest_output(result.stdout)
    if "note_path" not in parsed or "metadata_path" not in parsed:
        raise RuntimeError(f"Ingest completed but expected output markers were missing for source: {source}")
    return parsed


def load_entry(ingest_result: dict[str, str]) -> dict[str, object]:
    metadata_path = Path(ingest_result["metadata_path"])
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return {
        "title": metadata.get("title", metadata_path.parent.name),
        "channel": metadata.get("channel_or_author", ""),
        "duration": metadata.get("duration", ""),
        "transcript_source": metadata.get("transcript_source", ""),
        "classification": (metadata.get("classification") or {}).get("type", ""),
        "keywords": metadata.get("analysis_keywords") or [],
        "source_url": metadata.get("source_url", ""),
        "note_path": ingest_result["note_path"],
        "metadata_path": ingest_result["metadata_path"],
    }


def copy_entry_to_local_library(entry: dict[str, object], batch_dir: Path, index: int) -> dict[str, object]:
    stem = slugged_note_stem(index, str(entry["title"]))
    note_dest = batch_dir / f"{stem}.md"
    metadata_dest = batch_dir / f"{stem}.metadata.json"
    shutil.copy2(Path(str(entry["note_path"])), note_dest)
    shutil.copy2(Path(str(entry["metadata_path"])), metadata_dest)

    updated = dict(entry)
    updated["note_path"] = str(note_dest)
    updated["metadata_path"] = str(metadata_dest)
    return updated


def build_batch_index(*, batch_name: str, entries: list[dict[str, object]]) -> str:
    lines = [
        f"# Operational video batch — {batch_name}",
        "",
        "First real local research batch exported from `video-research-ingest` into the temporary local library.",
        "",
        "## Included videos",
        "",
    ]

    for idx, entry in enumerate(entries, start=1):
        keywords = ", ".join(entry.get("keywords") or [])
        lines.extend(
            [
                f"### {idx}. {entry['title']}",
                f"- Channel: {entry['channel']}",
                f"- Duration: {entry['duration']}",
                f"- Transcript source: {entry['transcript_source']}",
                f"- Classification: {entry['classification']}",
                f"- Keywords: {keywords}",
                f"- Source URL: {entry['source_url']}",
                f"- Local note: `{entry['note_path']}`",
                f"- Local metadata: `{entry['metadata_path']}`",
                "",
                "#### Review status",
                "- Worth keeping? [ ] yes [ ] maybe [ ] no",
                "- Export to Obsidian later? [ ] yes [ ] maybe [ ] no",
                "- What is worth keeping from this video?",
                "- What is weak / noisy / promotional?",
                "- Best follow-up action:",
                "",
            ]
        )

    return "\n".join(lines).strip() + "\n"


def main() -> None:
    args = parse_args()
    sources = parse_source_list(Path(args.input_file).expanduser().resolve())
    if not sources:
        raise SystemExit("No sources found in input file.")

    copied_entries: list[dict[str, object]] = []
    batch_dir = ensure_dir(LOCAL_LIBRARY_NOTES_DIR / args.batch_name)

    for index, source in enumerate(sources, start=1):
        ingest_result = run_ingest(source)
        entry = load_entry(ingest_result)
        if args.skip_local_library_copy:
            copied_entries.append(entry)
        else:
            copied_entries.append(copy_entry_to_local_library(entry, batch_dir, index))
        print(f"completed[{index}]={entry['title']}")

    index_path = batch_dir / "INDEX.md"
    index_path.write_text(build_batch_index(batch_name=args.batch_name, entries=copied_entries), encoding="utf-8")
    print(f"batch_dir={batch_dir}")
    print(f"index_path={index_path}")
    print(f"count={len(copied_entries)}")


if __name__ == "__main__":
    main()
