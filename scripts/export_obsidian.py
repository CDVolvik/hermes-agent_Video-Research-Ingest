"""Obsidian export helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import shutil

from utils import ensure_dir, get_obsidian_subfolder, get_obsidian_vault_path


def export_note_to_obsidian(note_path: Path) -> Path:
    vault = get_obsidian_vault_path()
    if vault is None:
        raise RuntimeError("OBSIDIAN_VAULT_PATH is not set")

    year = datetime.now(timezone.utc).strftime("%Y")
    month = datetime.now(timezone.utc).strftime("%m")
    target_dir = ensure_dir(vault / get_obsidian_subfolder() / year / month)
    target_path = target_dir / note_path.name
    shutil.copy2(note_path, target_path)
    return target_path
