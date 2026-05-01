from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from utils import load_template, render_template
from markdown import build_note


def test_build_note_writes_frontmatter(tmp_path):
    context = {
        "title": "Test Video",
        "source_url": "https://example.com/video",
        "source_file": "",
        "video_platform": "youtube",
        "date_ingested": "2026-04-30",
        "duration": "00:01:00",
        "channel_or_author": "Tester",
        "transcript_text": "Hello world",
        "frame_index": "- `frames/frame_0001.jpg` — Frame 1",
        "source_metadata_block": "{}",
        "metadata_json": {"title": "Test Video"},
        "template_name": "default-video-note.md",
        "classification_type": "inspiration",
        "classification_confidence": "pending-review",
        "reviewer_feedback": "- Strong workflow idea",
    }
    note_path = build_note(tmp_path, context)
    text = note_path.read_text(encoding="utf-8")
    assert 'title: "Test Video"' in text
    assert "## Classification" in text
    assert "- Type: inspiration" in text
    assert "## Reviewer Feedback" in text
    assert "- Strong workflow idea" in text
    assert "## Transcript" in text
    assert "Hello world" in text
    assert (tmp_path / "metadata.json").exists()
