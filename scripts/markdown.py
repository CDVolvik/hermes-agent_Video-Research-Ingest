"""Markdown generation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from utils import load_template, render_template, write_json


def build_note(work_dir: Path, context: dict[str, Any]) -> Path:
    template_name = context.get("template_name") or "default-video-note.md"
    template = load_template(template_name)
    rendered = render_template(template, context)

    sections = {
        "## Executive Summary": context.get("executive_summary", "Pending human summary."),
        "## Classification": context.get(
            "classification_block",
            f"- Type: {context.get('classification_type', 'inspiration')}\n- Confidence: {context.get('classification_confidence', 'pending-review')}",
        ),
        "## Key Insights": context.get("key_insights", "- Pending review"),
        "## Timestamped Notes": context.get("timestamped_notes", "- Pending review"),
        "## Transcript": context.get("transcript_text", ""),
        "## Frame Index": context.get("frame_index", "- No frames extracted"),
        "## Reviewer Feedback": context.get("reviewer_feedback", "- Pending human feedback"),
        "## Suggested Follow-ups": context.get("suggested_followups", "- Review and enrich the note"),
        "## Source Metadata": context.get("source_metadata_block", "{}"),
    }

    for heading, body in sections.items():
        rendered = rendered.replace(f"{heading}\n", f"{heading}\n\n{body}\n")

    note_path = work_dir / "note.md"
    note_path.write_text(rendered, encoding="utf-8")
    write_json(work_dir / "metadata.json", context.get("metadata_json", {}))
    return note_path
