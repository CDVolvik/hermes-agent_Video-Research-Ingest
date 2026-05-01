# video-research-ingest

Free-first, local-first, Hermes-compatible workflow for turning videos into structured research notes.

It is built to work even if you do **not** have Obsidian Sync, premium SaaS tooling, or paid APIs.

## What it does
Given a local video file or public video URL, the pipeline can generate:
- `note.md`
- `metadata.json`
- `transcript.txt`
- `frames/`
- optional `transcript.vtt`
- optional `audio.mp3`
- optional export into an Obsidian vault later

## Why this repo exists
This project is meant to be useful in a practical creator/research workflow:
- save ideas and inspirations from videos
- build a local library before connecting Obsidian
- avoid paid lock-in where possible
- keep artifacts portable and human-readable
- let agents and humans both use the same pipeline

## Current status
This repository started as a scaffold and is now a working local MVP.

### Working now
- ingest a **local video file**
- ingest a **video URL** via `yt-dlp`
- extract metadata with `ffprobe`
- extract representative frames with `ffmpeg`
- prefer **English subtitles first**, then configured fallback subtitle languages
- default fallback subtitle language is **Spanish** unless the user overrides it
- fall back to **local `faster-whisper` transcription** when subtitles are missing
- optionally fall back to an **OpenAI-compatible transcription API** if configured
- generate markdown notes and structured artifacts
- generate a lightweight first-pass analysis block for summary, classification, insights, and follow-ups
- use domain-aware heuristics so software, AI workflow, knowledge-system, and gaming/gold-making videos do not all get summarized with the same frame
- keep `metadata.json` curated and store full raw downloader output separately when available
- optionally export the final note to an Obsidian vault

### Current limitations
- first-pass note analysis is heuristic and still needs human review on messy auto-captions
- rolling auto-captions can still create awkward sentence fragments in timestamped notes
- creator videos with heavy CTA/promo sections can still leak marketing language into insights unless filtered further
- frame selection is simple and can be improved for longer videos
- API transcription fallback is optional but not required for the intended workflow
- Obsidian export is path-based; full sync strategy is intentionally out of scope

## Recommended fallback strategy
The default transcription chain is:
1. subtitles/VTT first
2. local `faster-whisper`
3. optional OpenAI-compatible API
4. empty transcript with explicit metadata marker if none are available

This keeps the tool:
- free-first
- local-first
- easy to adopt
- still extensible for teams that want hosted APIs later

## Recommended project location
Current working location:
- `/home/carli/video-research-ingest`

Why this is a good default:
- fast to develop and test inside WSL/Linux
- keeps the repo separate from the Obsidian vault
- avoids polluting notes with temp artifacts
- easy to push to GitHub later
- safer for Windows/cloud-backed vault setups

## Installation
### Prerequisites
Required binaries:
- `ffmpeg`
- `ffprobe`
- `yt-dlp` for URL ingest

Python packages currently used:
```bash
pip install -r requirements.txt
```

### Environment check
```bash
python3 scripts/setup.py
```

## Configuration
Copy values from `.env.example` into your shell, task runner, or environment manager.

Subtitle language behavior:
- primary default is English: `VIDEO_RESEARCH_PRIMARY_SUBTITLE_LANGS=en.*,en`
- fallback default is Spanish: `VIDEO_RESEARCH_FALLBACK_SUBTITLE_LANGS=es.*,es`
- public-facing agents/integrations should either:
  - ask the user what fallback language(s) they want, or
  - clearly state that Spanish is the default fallback if the user does not choose one

Key variables:
- `VIDEO_RESEARCH_PRIMARY_SUBTITLE_LANGS=en.*,en`
- `VIDEO_RESEARCH_FALLBACK_SUBTITLE_LANGS=es.*,es`
- `VIDEO_RESEARCH_TRANSCRIBER=auto`
- `VIDEO_RESEARCH_WHISPER_MODEL=base`
- `VIDEO_RESEARCH_WHISPER_DEVICE=auto`
- `VIDEO_RESEARCH_WHISPER_COMPUTE_TYPE=int8`
- `OBSIDIAN_VAULT_PATH=`
- `VIDEO_RESEARCH_INGEST_SUBFOLDER=Research/Video Research Ingest`
- `VIDEO_RESEARCH_INGEST_OUTPUT_DIR=./output`

Optional API-only variables:
- `OPENAI_API_KEY=***`
- `GROQ_API_KEY=***`
- `VIDEO_RESEARCH_TRANSCRIBE_BASE_URL=`
- `VIDEO_RESEARCH_OPENAI_TRANSCRIBE_MODEL=whisper-1`

## Quick start
### 1. Ingest a local video
```bash
python3 scripts/ingest.py --input /path/to/video.mp4
```

### 2. Ingest a URL
```bash
python3 scripts/ingest.py --input "https://www.youtube.com/watch?v=..."
```

### 3. Export note into Obsidian later
```bash
export OBSIDIAN_VAULT_PATH="/path/to/vault"
python3 scripts/ingest.py --input /path/to/video.mp4 --export-obsidian
```

## Output layout
Generated runs are written under:
- `output/<timestamp>-<slug>/`

Each run produces:
- `note.md`
- `metadata.json`
- `frames/`
- `transcript.txt`
- optionally `transcript.vtt`
- optionally `audio.mp3`

## Local-first note workflow
If you are not ready to sync Obsidian yet, keep notes local first.

Example local holding structure:
- `local-library/incoming/`
- `local-library/processed/`
- `local-library/notes/`

This supports a practical workflow:
1. capture video or link
2. ingest locally
3. review/edit note locally
4. later bulk export into Obsidian when your vault is ready

## Agent integration
This repo is intentionally agent-friendly.

For agent instructions, see:
- `AGENTS.md`

For analysis heuristics and hardening notes, see:
- `references/first-pass-analysis-hardening.md`

For a representative generated note, see:
- `examples/sample-output.md`

Recommended agent behavior:
- run the pipeline, then inspect generated files
- read `metadata.json` and check `transcript_source`
- never assume transcript quality without checking artifacts
- ask the user for preferred fallback subtitle language(s) during setup when possible
- if the user does not choose, use the repo default fallback of Spanish
- keep outputs human-editable and portable
- avoid hard-coding private vault paths or paid-provider assumptions

## Good initiative ideas for contributors
Useful next improvements that still preserve the repo's philosophy:
- improve timestamp extraction and note anchors
- make first-pass summaries more semantically robust on noisy subtitle streams
- improve frame sampling for long videos
- add OCR/vision analysis as optional secondary passes
- support batch ingest folders
- support a markdown index of processed videos

## Tests
```bash
pytest tests -q
```

## Suggested public positioning
A good way to describe this repo publicly:

> A free-first, local-first video research ingest pipeline for Hermes, Obsidian, and human-readable knowledge workflows.

## License
MIT. See `LICENSE`.
