"""Frame extraction helpers."""

from __future__ import annotations

from pathlib import Path

from utils import ensure_dir, run_command, which_required


def extract_representative_frames(video_path: Path, frames_dir: Path, frame_count: int = 4) -> list[dict]:
    which_required("ffmpeg")
    ensure_dir(frames_dir)

    output_pattern = frames_dir / "frame_%04d.jpg"
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            "fps=1",
            "-frames:v",
            str(frame_count),
            str(output_pattern),
        ]
    )

    frames = sorted(frames_dir.glob("frame_*.jpg"))
    results = []
    for idx, frame in enumerate(frames, start=1):
        results.append(
            {
                "path": str(frame),
                "relative_path": f"frames/{frame.name}",
                "label": f"Frame {idx}",
            }
        )
    return results
