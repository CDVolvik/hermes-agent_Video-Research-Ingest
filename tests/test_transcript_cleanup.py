from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from transcript import resolve_transcriber_backend
from utils import clean_vtt_text


def test_clean_vtt_text_removes_timestamps_and_tags():
    raw = """WEBVTT

Kind: captions
Language: en

1
00:00:00.000 --> 00:00:02.000
<c.colorE5E5E5>Hello</c>
<c.colorE5E5E5>Hello</c>

2
00:00:02.000 --> 00:00:04.000
[Music]
World
World
"""
    cleaned = clean_vtt_text(raw)
    assert cleaned == "Hello\nWorld"


def test_resolve_transcriber_backend_defaults_to_auto(monkeypatch):
    monkeypatch.delenv("VIDEO_RESEARCH_TRANSCRIBER", raising=False)
    assert resolve_transcriber_backend() == "auto"



def test_resolve_transcriber_backend_rejects_unknown_value(monkeypatch):
    monkeypatch.setenv("VIDEO_RESEARCH_TRANSCRIBER", "something-else")
    assert resolve_transcriber_backend() == "auto"
