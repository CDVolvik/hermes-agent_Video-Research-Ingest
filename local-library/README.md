# Local video note holding area

This folder is the temporary local library for video research ingest before Obsidian Sync is set up.

## Folders
- `incoming/` — videos dropped here for future processing
- `processed/` — original videos or references after ingest
- `notes/` — exported markdown notes kept locally until Obsidian is connected

## Current workflow
1. User sends/provides a video or a batch list.
2. Hermes ingests it with the `video-research-ingest` pipeline.
3. Generated markdown notes stay local for now.
4. Review the batch with `REVIEW-RUBRIC.md`.
5. Once Obsidian Sync or the final vault path is ready, only the best notes should be bulk-moved into the chosen Obsidian folder.

## Repeatable batch workflow
Create a plain-text file in `incoming/`, for example `incoming/example-batch.txt`, with one source per line.

Recommended permanent starting files:
- `incoming/ai-workflows.txt`
- `incoming/r21-ops.txt`
- `incoming/wow-goldmaking.txt`

These are meant to be stable standing queues, not one-off scratch files. Add new sources to the right lane, run a batch when ready, then review the generated notes before deciding what is worth keeping.

Then run:

```bash
python3 scripts/batch_ingest.py \
  --input-file local-library/incoming/example-batch.txt \
  --batch-name 2026-05-01-example-batch
```

This creates a batch folder under `notes/` with:
- copied note files
- copied metadata files
- an `INDEX.md` overview with review prompts

## Review rubric
Use:
- `local-library/REVIEW-RUBRIC.md`

## Suggested future Obsidian destination
- `Ideas/Video Inspirations/`
- or another folder you choose later.

## Closeout operating rule
- Treat the current pipeline as finished enough for real use.
- Do not add new features until repeated real usage shows a clear pain point.
- A good trigger for the next upgrade is friction that appears across at least 3 real batches.
