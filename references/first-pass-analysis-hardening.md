# First-pass analysis hardening

This repo intentionally keeps first-pass analysis **deterministic, lightweight, and editable**.

## Current approach
The analysis layer now tries to improve note quality without adding another paid or opaque LLM stage.

It currently does four main things:

1. **Domain detection**
   - tries to distinguish between patterns like:
     - AI/design workflow
     - software build walkthrough
     - agent memory / knowledge-system explanation
     - gaming / gold-making guide
     - general workflow content

2. **Topic-aware summary wording**
   - avoids using one generic summary frame for every video
   - changes the executive-summary language based on the detected domain

3. **Keyword extraction with title/tag weighting**
   - favors title terms and downloader tags over noisy repeated transcript filler
   - blocks common junk tokens like `going`, `right`, `here`, `some`, `make`

4. **Broader theme detection**
   - detects themes such as:
     - setup
     - workflow
     - prompting
     - automation
     - editing
     - quality control
     - memory system
     - configuration
     - economy
     - professions
     - creator business

## Why this exists
YouTube auto-captions are noisy, repetitive, and often domain-specific.
A summary system that works on one AI workflow video can fail badly on:
- software setup walkthroughs
- gaming/economy guides
- knowledge-management videos
- hybrid tutorial + sales-funnel content

This hardening pass is meant to keep the repo usable as a **public foundation** for many kinds of videos, not only one creator niche.

## Known limits
This is still a first-pass heuristic layer.

Current weak spots:
- rolling captions can still produce awkward fragments in timestamped notes
- theme detection can still be too broad when descriptions contain marketing language
- summaries can still pick a weaker sentence if the transcript is especially messy
- confidence scores are heuristic, not calibrated

## Public repo principle
The repo should stay:
- free-first
- local-first
- human-readable
- agent-friendly
- easy to inspect and modify

If higher-quality summaries are needed later, prefer making an **optional** semantic pass rather than replacing the deterministic first pass.

## Next likely improvements
- cleaner sentence stitching from rolling captions
- stronger de-promo filtering for creator/community CTA language
- optional chapter extraction from timestamp clusters
- optional second-pass semantic enrichment behind a flag
