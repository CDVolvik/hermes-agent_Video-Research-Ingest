# AGENTS.md

This repository is designed so human users and coding/ops agents can integrate it safely.

## Purpose
Turn a local video file or public video URL into reusable research artifacts:
- `note.md`
- `metadata.json`
- `transcript.txt`
- `frames/`
- optional Obsidian export

## Recommended integration contract
Agents should treat this repo as a filesystem pipeline, not as a chat-only summarizer.

### Inputs
Provide one of:
- local file path
- public video URL

### Main command
```bash
python3 scripts/ingest.py --input "<video-path-or-url>"
```

Optional Obsidian export:
```bash
python3 scripts/ingest.py --input "<video-path-or-url>" --export-obsidian
```

### Expected outputs
Each run creates:
```text
output/<timestamp>-<slug>/
  note.md
  metadata.json
  transcript.txt
  frames/
```

Agents should read these files after execution instead of assuming success from exit code alone.

## Fallback behavior
The pipeline uses this order:
1. subtitles/VTT when available
2. local `faster-whisper` transcription when installed
3. optional OpenAI-compatible API when configured
4. empty transcript with metadata marker if none of the above are available

Subtitle language defaults:
- primary: English
- fallback: Spanish

Agents should not silently assume the user's fallback language preferences in long-term setups.
When onboarding or configuring the repo for someone else, agents should either:
- ask which fallback subtitle language(s) the user prefers, or
- explicitly state that Spanish is the default fallback when no preference is provided

Agents should inspect `metadata.json` field `transcript_source`.

## Safe usage rules
- Do not hard-code private vault paths.
- Keep generated output outside the Obsidian vault until export time.
- Do not commit `output/`, `.env`, or user media files.
- Do not assume API keys exist.
- Prefer free/local defaults.

## Environment variables agents may set
- `VIDEO_RESEARCH_TRANSCRIBER`
- `VIDEO_RESEARCH_WHISPER_MODEL`
- `VIDEO_RESEARCH_WHISPER_DEVICE`
- `VIDEO_RESEARCH_WHISPER_COMPUTE_TYPE`
- `VIDEO_RESEARCH_TRANSCRIBE_BASE_URL`
- `VIDEO_RESEARCH_OPENAI_TRANSCRIBE_MODEL`
- `OPENAI_API_KEY`
- `GROQ_API_KEY`
- `OBSIDIAN_VAULT_PATH`
- `VIDEO_RESEARCH_INGEST_SUBFOLDER`
- `VIDEO_RESEARCH_INGEST_OUTPUT_DIR`

## Suggested agent workflow
1. Run `python3 scripts/setup.py`
2. Ingest the video
3. Read `metadata.json`
4. Read `note.md`
5. If `transcript_source` indicates no transcript, report limitation clearly
6. Export to Obsidian only if the vault path is confirmed

## Good initiative for downstream agents
A good agent integration should:
- classify the video as idea/inspiration/research/reference
- append lightweight tags
- summarize key moments after note generation
- keep human-editable markdown as the source of truth

Avoid turning this into a black-box proprietary workflow. Keep outputs portable and inspectable.
