"""Subtitle/transcript helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import os

from utils import clean_vtt_text, run_command_optional, which_required

try:
    from faster_whisper import WhisperModel
except Exception:  # pragma: no cover - optional dependency
    WhisperModel = None  # type: ignore[assignment]

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore[assignment]


DEFAULT_LOCAL_MODEL = "base"
DEFAULT_DEVICE = "auto"
DEFAULT_COMPUTE_TYPE = "int8"


def build_transcript(video_path: Path, subtitle_path: Path | None, work_dir: Path) -> dict[str, Any]:
    transcript_vtt = work_dir / "transcript.vtt"
    transcript_txt = work_dir / "transcript.txt"

    if subtitle_path and subtitle_path.exists():
        raw = subtitle_path.read_text(encoding="utf-8", errors="ignore")
        transcript_vtt.write_text(raw, encoding="utf-8")
        cleaned = clean_vtt_text(raw)
        transcript_txt.write_text(cleaned, encoding="utf-8")
        return {
            "transcript_text": cleaned,
            "transcript_source": "subtitles",
            "transcript_path": transcript_txt,
        }

    audio_path = work_dir / "audio.mp3"
    extracted = extract_audio(video_path, audio_path)
    if not extracted:
        transcript_txt.write_text("", encoding="utf-8")
        return {
            "transcript_text": "",
            "transcript_source": "none",
            "transcript_path": transcript_txt,
        }

    backend = resolve_transcriber_backend()
    transcript_text = ""
    transcript_source = "audio-extracted-no-transcriber-configured"

    local_enabled = backend in {"auto", "local"}
    api_enabled = backend in {"auto", "openai"}

    if local_enabled:
        transcript_text = transcribe_with_faster_whisper(audio_path)
        if transcript_text:
            transcript_source = f"faster-whisper:{get_local_model_name()}"
        elif WhisperModel is not None:
            transcript_source = "local-transcriber-no-result"

    if not transcript_text and api_enabled:
        transcript_text = transcribe_with_openai_compatible(audio_path)
        if transcript_text:
            transcript_source = "openai-compatible-api"
        elif api_transcriber_configured():
            transcript_source = "api-transcriber-no-result"

    if backend == "none":
        transcript_source = "transcription-disabled"

    transcript_txt.write_text(transcript_text, encoding="utf-8")
    return {
        "transcript_text": transcript_text,
        "transcript_source": transcript_source,
        "transcript_path": transcript_txt,
    }



def resolve_transcriber_backend() -> str:
    configured = os.getenv("VIDEO_RESEARCH_TRANSCRIBER", "auto").strip().lower()
    if configured in {"auto", "local", "openai", "none"}:
        return configured
    return "auto"



def api_transcriber_configured() -> bool:
    return bool((os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")) and OpenAI is not None)



def get_local_model_name() -> str:
    return os.getenv("VIDEO_RESEARCH_WHISPER_MODEL", DEFAULT_LOCAL_MODEL).strip() or DEFAULT_LOCAL_MODEL



def transcribe_with_faster_whisper(audio_path: Path) -> str:
    if WhisperModel is None:
        return ""

    try:
        model = WhisperModel(
            get_local_model_name(),
            device=os.getenv("VIDEO_RESEARCH_WHISPER_DEVICE", DEFAULT_DEVICE).strip() or DEFAULT_DEVICE,
            compute_type=os.getenv("VIDEO_RESEARCH_WHISPER_COMPUTE_TYPE", DEFAULT_COMPUTE_TYPE).strip() or DEFAULT_COMPUTE_TYPE,
        )
        segments, _info = model.transcribe(str(audio_path))
        lines = [segment.text.strip() for segment in segments if segment.text.strip()]
        return "\n".join(lines).strip()
    except Exception:
        return ""



def transcribe_with_openai_compatible(audio_path: Path) -> str:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key or OpenAI is None:
        return ""

    base_url = os.getenv("VIDEO_RESEARCH_TRANSCRIBE_BASE_URL", "").strip() or None
    model = os.getenv("VIDEO_RESEARCH_OPENAI_TRANSCRIBE_MODEL", "whisper-1").strip() or "whisper-1"

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        with audio_path.open("rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
            )
        text = getattr(transcript, "text", "")
        return (text or "").strip()
    except Exception:
        return ""



def extract_audio(video_path: Path, audio_path: Path) -> bool:
    which_required("ffmpeg")
    result = run_command_optional(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-acodec",
            "libmp3lame",
            str(audio_path),
        ]
    )
    return result.returncode == 0 and audio_path.exists()
