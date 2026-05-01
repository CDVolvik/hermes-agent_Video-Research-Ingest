"""Video download / acquisition helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os
import shutil

from utils import ensure_dir, is_url, run_command_optional, slugify, which_required


def acquire_source(input_value: str, work_dir: Path) -> dict[str, Any]:
    if is_url(input_value):
        return download_video(input_value, work_dir)
    local_path = Path(input_value).expanduser().resolve()
    if not local_path.exists():
        raise FileNotFoundError(f"Local video file not found: {local_path}")
    ext = local_path.suffix or ".mp4"
    copied = work_dir / f"source{ext}"
    shutil.copy2(local_path, copied)
    return {
        "source_url": "",
        "source_file": str(local_path),
        "video_path": copied,
        "title": local_path.stem,
        "video_platform": "local",
        "channel_or_author": "",
        "subtitle_path": None,
        "download_metadata": {},
    }



def download_video(url: str, work_dir: Path) -> dict[str, Any]:
    which_required("yt-dlp")
    ensure_dir(work_dir)
    base = work_dir / "source"
    output_pattern = str(base) + ".%(ext)s"

    download_with_fallbacks(url, output_pattern, work_dir)

    video_candidates = [
        p for p in work_dir.iterdir() if p.is_file() and p.name.startswith("source.") and p.suffix != ".json"
    ]
    subtitle_candidates = sorted(
        [p for p in work_dir.iterdir() if p.is_file() and p.name.startswith("source.") and ".vtt" in p.name]
    )
    info_candidates = [p for p in work_dir.iterdir() if p.is_file() and p.name.startswith("source.") and p.suffix == ".json"]

    video_path = next((p for p in video_candidates if ".vtt" not in p.name), None)
    info_path = info_candidates[0] if info_candidates else None
    if video_path is None:
        raise RuntimeError("yt-dlp completed but no source video file was found")

    metadata = {}
    if info_path:
        metadata = json.loads(info_path.read_text(encoding="utf-8"))

    title = metadata.get("title") or slugify(url)
    channel = metadata.get("channel") or metadata.get("uploader") or ""
    platform = metadata.get("extractor_key") or metadata.get("extractor") or "other"

    return {
        "source_url": url,
        "source_file": "",
        "video_path": video_path,
        "title": title,
        "video_platform": str(platform).lower(),
        "channel_or_author": channel,
        "subtitle_path": pick_best_subtitle(subtitle_candidates),
        "download_metadata": metadata,
    }



def download_with_fallbacks(url: str, output_pattern: str, work_dir: Path) -> None:
    base_args = [
        "yt-dlp",
        "--no-playlist",
        "--write-info-json",
        "-o",
        output_pattern,
    ]

    primary_languages = os.getenv("VIDEO_RESEARCH_PRIMARY_SUBTITLE_LANGS", "en.*,en")
    fallback_languages = os.getenv("VIDEO_RESEARCH_FALLBACK_SUBTITLE_LANGS", "es.*,es")

    attempts = [
        [
            *base_args,
            "--write-auto-sub",
            "--write-sub",
            "--sub-langs",
            primary_languages,
            "--sub-format",
            "vtt",
            url,
        ],
        [
            *base_args,
            "--write-auto-sub",
            "--write-sub",
            "--sub-langs",
            fallback_languages,
            "--sub-format",
            "vtt",
            url,
        ],
        [*base_args, url],
    ]

    last_error = ""
    for args in attempts:
        result = run_command_optional(args, cwd=work_dir)
        if result.returncode == 0:
            return
        last_error = (result.stderr or result.stdout or "").strip()

    raise RuntimeError(f"yt-dlp failed after fallback attempts: {last_error}")



def pick_best_subtitle(candidates: list[Path]) -> Path | None:
    if not candidates:
        return None

    preferred_tokens = [".en-orig.", ".en.", ".es."]
    for token in preferred_tokens:
        match = next((p for p in candidates if token in p.name), None)
        if match:
            return match
    return candidates[0]
