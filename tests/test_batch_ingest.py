from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from batch_ingest import build_batch_index, parse_source_list, slugged_note_stem


def test_parse_source_list_ignores_comments_and_blank_lines(tmp_path):
    source_file = tmp_path / "sources.txt"
    source_file.write_text(
        """
# batch for agent videos
https://www.youtube.com/watch?v=abc123

  https://example.com/video.mp4  
# another comment
/home/carli/Videos/local-demo.mp4
""",
        encoding="utf-8",
    )

    sources = parse_source_list(source_file)

    assert sources == [
        "https://www.youtube.com/watch?v=abc123",
        "https://example.com/video.mp4",
        "/home/carli/Videos/local-demo.mp4",
    ]


def test_slugged_note_stem_uses_index_and_title_slug():
    stem = slugged_note_stem(3, "Claude Code + Higgsfield MCP = Content MACHINE")

    assert stem == "03-claude-code-higgsfield-mcp-content-machine"


def test_build_batch_index_includes_review_fields():
    entries = [
        {
            "title": "My Claude Code Can INSTANTLY Watch Any Video (Here's How)",
            "channel": "Brad | AI & Automation",
            "duration": "00:08:36",
            "transcript_source": "subtitles",
            "classification": "tutorial",
            "keywords": ["claude", "frames", "transcript"],
            "source_url": "https://www.youtube.com/watch?v=QZMljuD10sU",
            "note_path": "/tmp/04-watch-any-video.md",
            "metadata_path": "/tmp/04-watch-any-video.metadata.json",
        }
    ]

    content = build_batch_index(batch_name="2026-05-01-youtube-agent-workflows", entries=entries)

    assert "# Operational video batch — 2026-05-01-youtube-agent-workflows" in content
    assert "## Included videos" in content
    assert "## Review status" in content
    assert "Export to Obsidian later?" in content
    assert "What is worth keeping from this video?" in content
    assert "My Claude Code Can INSTANTLY Watch Any Video" in content
