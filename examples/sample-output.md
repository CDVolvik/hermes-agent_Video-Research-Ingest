# Sample Output

Representative generated note excerpt from a real public YouTube ingest.
This example is intentionally shortened so the repo shows the artifact shape without dumping a full transcript into the docs.

```md
---
title: "OpenClaw's New Memory System Is Crazy (Dreaming, Memory Wiki & Active Memory)"
source_type: video
source_url: "https://www.youtube.com/watch?v=3BZNtH_51Xk"
video_platform: "youtube"
date_ingested: "2026-05-01"
duration: "00:06:58"
channel_or_author: "Openclaw Labs"
tags:
  - video
  - research
  - ingest
status: processed
---

# OpenClaw's New Memory System Is Crazy (Dreaming, Memory Wiki & Active Memory)

## Executive Summary
- This looks like a **workflow** video focused on an agent memory architecture and setup explanation rather than entertainment-only commentary.
- Main topics: setup, workflow, prompting, automation, editing.
- Practical value: useful for understanding how dreaming, memory wiki, and active memory fit together.

## Classification
- Type: workflow
- Confidence: medium
- Domain: agent-memory
- Themes: setup, workflow, prompting, automation, editing
- Keywords: memory, dreaming, wiki, obsidian, recall, agent

## Key Insights
- Dreaming reviews recent short-term material and only promotes stronger long-term patterns.
- Memory wiki creates a more structured knowledge layer with contradiction and freshness tracking.
- Active memory runs a bounded recall pass before the main agent responds.

## Timestamped Notes
- 00:00:07 — Three updates just dropped that completely change how your agent stores, organizes, and recalls information.
- 00:02:19 — Dreaming writes a human-readable dream diary into `dreams.md`.
- 00:04:06 — Memory wiki adds search, apply, and lint tooling around structured knowledge.
```

Typical full run outputs also include:
- `metadata.json`
- `transcript.txt`
- `frames/`
- optional `transcript.vtt`
- optional `audio.mp3`
