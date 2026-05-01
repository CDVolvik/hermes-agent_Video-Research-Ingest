---
name: video-research-ingest
description: Use when converting a video URL or local recording into structured research artifacts and human-editable markdown.
version: 1.1.0
author: CDVolvik + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [video, research, obsidian, markdown, ingestion, transcript]
    related_skills: [obsidian, hermes-agent]
---

# video-research-ingest

## Purpose
Turn a local video file or public video URL into reusable research artifacts:
- `note.md`
- `metadata.json`
- `transcript.txt`
- `frames/`
- optional `transcript.vtt`
- optional Obsidian export

## Repo philosophy
- free-first
- local-first
- human-editable outputs
- agent-friendly filesystem workflow
- optional paid/API fallback, never required by default

## Main command
```bash
python3 scripts/ingest.py --input "<video-path-or-url>"
```

Optional Obsidian export:
```bash
python3 scripts/ingest.py --input "<video-path-or-url>" --export-obsidian
```

Environment check:
```bash
python3 scripts/setup.py
```

Tests:
```bash
pytest tests -q
```

## Fallback order
1. subtitles/VTT when available
2. local `faster-whisper`
3. optional OpenAI-compatible API
4. empty transcript with explicit metadata marker if none are available

Default subtitle language behavior:
- primary: English
- fallback: Spanish

When configuring this for another user, either ask their preferred fallback subtitle language(s) or state clearly that Spanish is the default fallback.

## Agent workflow
1. Run `python3 scripts/setup.py`
2. Run the ingest command
3. Read `metadata.json`
4. Read `note.md`
5. Check `metadata.json["transcript_source"]`
6. Report limitations if transcript quality is weak or missing
7. Export to Obsidian only if the vault path is confirmed

## Important output checks
Do not assume success from exit code alone. Verify generated artifacts exist under:
```text
output/<timestamp>-<slug>/
```

At minimum, confirm:
- `note.md`
- `metadata.json`
- `transcript.txt`
- `frames/`

## Public repo notes
- keep `output/`, `.env`, and personal media files out of git
- do not hard-code private vault paths
- keep sample notes representative but lightweight
- keep first-pass analysis deterministic and editable
