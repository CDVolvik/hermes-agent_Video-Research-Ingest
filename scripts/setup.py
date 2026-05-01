#!/usr/bin/env python3
"""Environment and dependency checks for video-research-ingest."""

from pathlib import Path
import importlib.util
import os
import shutil


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None



def main() -> None:
    print("video-research-ingest setup check")
    print("project_root =", Path(__file__).resolve().parents[1])
    print("yt_dlp_binary =", os.getenv("YT_DLP_PATH", shutil.which("yt-dlp") or ""))
    print("ffmpeg_binary =", shutil.which("ffmpeg") or "")
    print("ffprobe_binary =", shutil.which("ffprobe") or "")
    print("obsidian_vault_path =", os.getenv("OBSIDIAN_VAULT_PATH", ""))
    print("transcriber_backend =", os.getenv("VIDEO_RESEARCH_TRANSCRIBER", "auto"))
    print("local_whisper_model =", os.getenv("VIDEO_RESEARCH_WHISPER_MODEL", "base"))
    print("faster_whisper_installed =", module_available("faster_whisper"))
    print("openai_sdk_installed =", module_available("openai"))


if __name__ == "__main__":
    main()
