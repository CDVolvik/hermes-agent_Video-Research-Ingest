"""Utility helpers for video-research-ingest."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT_DIR / "templates"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "untitled-video"


def get_output_dir() -> Path:
    configured = os.getenv("VIDEO_RESEARCH_INGEST_OUTPUT_DIR", str(ROOT_DIR / "output"))
    return Path(configured).expanduser().resolve()


def get_obsidian_vault_path() -> Path | None:
    configured = os.getenv("OBSIDIAN_VAULT_PATH", "").strip()
    if not configured:
        return None
    return Path(configured).expanduser().resolve()


def get_obsidian_subfolder() -> str:
    return os.getenv(
        "VIDEO_RESEARCH_INGEST_SUBFOLDER",
        "Research/Video Research Ingest",
    ).strip("/")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def utc_timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def which_required(binary: str) -> str:
    resolved = shutil.which(binary)
    if not resolved:
        raise RuntimeError(f"Required binary not found: {binary}")
    return resolved


def run_command(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=True,
    )


def run_command_optional(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
    )


def load_template(name: str = "default-video-note.md") -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def render_template(template: str, context: dict[str, Any]) -> str:
    rendered = template
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{ {key} }}}}", str(value))
    return rendered


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def seconds_to_hhmmss(seconds: float | int | None) -> str:
    total = int(round(float(seconds or 0)))
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def probe_media(path: Path) -> dict[str, Any]:
    which_required("ffprobe")
    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-print_format",
            "json",
            str(path),
        ]
    )
    data = json.loads(result.stdout)
    fmt = data.get("format", {})
    return {
        "duration_seconds": float(fmt.get("duration") or 0),
        "size_bytes": int(fmt.get("size") or 0),
        "format_name": fmt.get("format_name", ""),
        "streams": data.get("streams", []),
    }


def clean_vtt_text(raw: str) -> str:
    lines: list[str] = []
    last_line = ""
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "WEBVTT":
            continue
        if re.match(r"^\d+$", stripped):
            continue
        if "-->" in stripped:
            continue
        if stripped.startswith("NOTE"):
            continue
        if stripped.startswith("Kind:") or stripped.startswith("Language:"):
            continue
        stripped = re.sub(r"<[^>]+>", "", stripped)
        stripped = re.sub(r"\[[^\]]+\]", "", stripped)
        stripped = re.sub(r"\s+", " ", stripped).strip()
        if stripped and stripped != last_line:
            lines.append(stripped)
            last_line = stripped
    return "\n".join(lines)
