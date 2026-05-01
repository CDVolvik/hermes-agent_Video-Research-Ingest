"""Lightweight first-pass analysis helpers for generated video notes."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
import re

from utils import seconds_to_hhmmss

STOPWORDS = {
    "a",
    "about",
    "after",
    "all",
    "also",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "back",
    "be",
    "because",
    "been",
    "being",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "doing",
    "done",
    "for",
    "from",
    "get",
    "going",
    "go",
    "got",
    "had",
    "has",
    "have",
    "here",
    "how",
    "i",
    "if",
    "im",
    "in",
    "into",
    "is",
    "it",
    "its",
    "just",
    "let",
    "lets",
    "like",
    "make",
    "more",
    "most",
    "my",
    "new",
    "now",
    "of",
    "okay",
    "on",
    "or",
    "our",
    "out",
    "over",
    "really",
    "right",
    "same",
    "see",
    "so",
    "some",
    "still",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "thing",
    "this",
    "those",
    "through",
    "to",
    "today",
    "too",
    "up",
    "use",
    "using",
    "very",
    "want",
    "was",
    "we",
    "well",
    "what",
    "when",
    "where",
    "which",
    "while",
    "will",
    "with",
    "without",
    "work",
    "would",
    "yeah",
    "you",
    "your",
}

LOW_SIGNAL_PREFIXES = (
    "all right",
    "alright",
    "and there we go",
    "great there we go",
    "join my free community",
    "join the free community",
    "what is up",
    "welcome back",
    "if that is interesting",
    "remember to subscribe",
    "thanks for watching",
)

THEME_LIBRARY = [
    ("setup", ["download", "install", "set up", "extension", "environment variable", "config", "enable", "turn it on"]),
    ("workflow", ["process", "workflow", "pipeline", "step", "first thing", "then once", "mental model"]),
    ("prompting", ["prompt", "brief", "spec", "propose", "instructions", "reference"]),
    ("automation", ["automate", "agent", "sub-agent", "parallel", "batch", "bulk"]),
    ("editing", ["edit", "editable", "layers", "canva", "magic layers", "tweak"]),
    ("quality control", ["higher resolution", "aspect ratio", "review", "checklist", "quality", "upscale"]),
    ("memory system", ["memory", "dreaming", "wiki", "active memory", "long-term", "recall"]),
    ("configuration", ["settings", "threshold", "score", "secret", "api key", "vault", "environment values"]),
    ("economy", ["gold", "profit", "auction house", "token", "market", "pricing", "orders"]),
    ("professions", ["profession", "blacksmithing", "enchanting", "tailoring", "inscription", "knowledge"]),
    ("creator business", ["client", "community", "masterclass", "members", "source code", "free community"]),
]

DOMAIN_RULES = [
    (
        "gaming-goldmaking",
        ["wow", "world of warcraft", "silvermoon", "gold", "auction house", "profession", "token", "blacksmithing", "enchanting"],
    ),
    (
        "agent-memory",
        ["dreaming", "memory wiki", "active memory", "long-term memory", "obsidian", "memory.md", "recall"],
    ),
    (
        "ai-design",
        ["canva", "poster", "design", "gpt image", "magic layers", "aspect ratio", "high-res"],
    ),
    (
        "agent-video-analysis",
        [
            "watch any video",
            "video analysis",
            "video research",
            "youtube video",
            "extracts frames",
            "reads the transcript",
            "transcript chunks",
            "frame context",
        ],
    ),
    (
        "software-build",
        ["calendly", "source code", "environment values", "spec", "build our own", "app", "repo"],
    ),
]

CLASSIFICATION_RULES = {
    "tutorial": ["beginner", "beginners", "course", "how to", "walk you through", "show you how", "set up", "guide"],
    "workflow": ["workflow", "process", "pipeline", "brief", "adapt", "bulk", "mental model", "step by step"],
    "inspiration": ["changed forever", "completely changed", "crazy", "powerful", "insane", "incredible"],
    "reference": ["dimensions", "resolution", "template", "settings", "threshold", "scored", "checklist"],
    "research": ["analysis", "compare", "benchmark", "study", "signals", "scored", "weights"],
}

SUMMARY_DOMAIN_LANGUAGE = {
    "gaming-goldmaking": "a practical gold-making method inside World of Warcraft rather than general commentary",
    "agent-memory": "an agent memory architecture and setup explanation rather than entertainment-only commentary",
    "ai-design": "an AI-assisted creative workflow rather than pure theory",
    "agent-video-analysis": "an agent-driven video analysis workflow rather than a generic coding demo",
    "software-build": "a build-and-ship walkthrough for a small software tool rather than abstract theory",
    "general": "a practical repeatable workflow rather than pure theory",
}

FOLLOWUP_LIBRARY = {
    "gaming-goldmaking": [
        "- Validate the method against your own realm economy before copying the exact craft mix.",
        "- Extract the repeatable weekly route into a short checklist by character/profession.",
    ],
    "agent-memory": [
        "- Verify which features are optional vs safe defaults before changing your production setup.",
        "- Turn the feature sequence into a short operator note: what it does, when to enable it, and what can break.",
    ],
    "software-build": [
        "- Verify the setup path on a clean machine so the walkthrough is not dependent on hidden local state.",
        "- Capture the exact prompt/spec pattern if the build result is worth reusing.",
    ],
    "ai-design": [
        "- Save the strongest prompt and review pattern as a reusable template before scaling it to client work.",
        "- Add a QA step before bulk generation goes to production use.",
    ],
    "agent-video-analysis": [
        "- Validate the workflow on a second video format so frame extraction and transcript handling are not overfit to one example.",
        "- Capture the exact agent input structure for frames, transcript chunks, and review notes before scaling the workflow.",
    ],
}


def analyze_transcript(
    *,
    title: str,
    transcript_text: str,
    transcript_vtt_path: Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = metadata or {}
    cues = parse_vtt_cues(transcript_vtt_path) if transcript_vtt_path and transcript_vtt_path.exists() else []
    sentences = split_sentences(transcript_text)
    context_text = build_context_text(title=title, transcript_text=transcript_text, metadata=metadata)
    domain = infer_domain(context_text)
    keywords = extract_keywords(title=title, transcript_text=transcript_text, metadata=metadata, domain=domain)
    classification = infer_classification(title=title, transcript_text=transcript_text, metadata=metadata, domain=domain)
    themes = detect_themes(cues, context_text)

    return {
        "domain": domain,
        "executive_summary": build_executive_summary(title, classification, themes, sentences, domain),
        "classification": classification,
        "keywords": keywords,
        "classification_block": build_classification_block(classification, themes, keywords, domain),
        "key_insights": build_key_insights(sentences, themes),
        "timestamped_notes": build_timestamped_notes(cues, themes),
        "reviewer_feedback": build_reviewer_feedback(classification, themes, domain),
        "suggested_followups": build_suggested_followups(classification, themes, domain),
    }


def build_context_text(*, title: str, transcript_text: str, metadata: dict[str, Any]) -> str:
    download_metadata = metadata.get("download_metadata") or {}
    fields = [
        title,
        transcript_text,
        metadata.get("channel_or_author", ""),
        " ".join(download_metadata.get("categories") or []),
        " ".join(download_metadata.get("tags") or []),
        download_metadata.get("description", ""),
    ]
    return "\n".join(part for part in fields if part)


def parse_vtt_cues(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []

    raw = path.read_text(encoding="utf-8", errors="ignore")
    cues: list[dict[str, Any]] = []
    current_start: int | None = None
    text_lines: list[str] = []

    def flush() -> None:
        nonlocal current_start, text_lines
        if current_start is None or not text_lines:
            current_start = None
            text_lines = []
            return
        cleaned = clean_caption_text(" ".join(text_lines))
        if cleaned:
            if not cues or normalize_text(cues[-1]["text"]) != normalize_text(cleaned):
                cues.append(
                    {
                        "start_seconds": current_start,
                        "timestamp": seconds_to_hhmmss(current_start),
                        "text": cleaned,
                    }
                )
        current_start = None
        text_lines = []

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped == "WEBVTT" or stripped.startswith("Kind:") or stripped.startswith("Language:"):
            continue
        if "-->" in stripped:
            flush()
            current_start = parse_timestamp_to_seconds(stripped.split("-->", 1)[0].strip())
            continue
        if re.match(r"^\d+$", stripped):
            continue
        text_lines.append(stripped)

    flush()
    return compact_cues(remove_rolling_caption_duplicates(cues))


def remove_rolling_caption_duplicates(cues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for index, cue in enumerate(cues):
        current = normalize_text(cue["text"])
        if not current:
            continue
        should_skip = False
        for lookahead in cues[index + 1 : index + 4]:
            future = normalize_text(lookahead["text"])
            if future.startswith(current) and len(future) > len(current):
                should_skip = True
                break
        if not should_skip:
            filtered.append(cue)
    return filtered


def compact_cues(cues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not cues:
        return []

    compacted: list[dict[str, Any]] = []
    current = dict(cues[0])

    for cue in cues[1:]:
        gap = cue["start_seconds"] - current["start_seconds"]
        current_text = current["text"]
        next_text = cue["text"]
        should_merge = (
            gap <= 14
            and len(current_text.split()) < 26
            and not re.search(r"[.!?]$", current_text)
            and starts_like_continuation(next_text)
        )
        if should_merge:
            merged_text = de_duplicate_overlap(current_text, next_text)
            current["text"] = merged_text
            continue
        compacted.append(current)
        current = dict(cue)

    compacted.append(current)
    return compacted


def starts_like_continuation(text: str) -> bool:
    lowered = text.lower()
    return bool(
        text[:1].islower()
        or re.match(r"^(and|but|or|so|because|then|when|with|to|for|of|in|on|if|we|you|it|they|this|that|these|those)\b", lowered)
    )


def de_duplicate_overlap(left: str, right: str) -> str:
    left_words = left.split()
    right_words = right.split()
    max_overlap = min(len(left_words), len(right_words), 8)
    for overlap in range(max_overlap, 0, -1):
        if [normalize_token(word) for word in left_words[-overlap:]] == [normalize_token(word) for word in right_words[:overlap]]:
            merged = left_words + right_words[overlap:]
            return " ".join(merged)
    return re.sub(r"\s+", " ", f"{left} {right}").strip()


def normalize_token(token: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", token.lower())


def parse_timestamp_to_seconds(value: str) -> int:
    match = re.match(r"(?:(\d{2}):)?(\d{2}):(\d{2})(?:\.\d+)?", value)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def clean_caption_text(text: str) -> str:
    text = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}><c>", " ", text)
    text = re.sub(r"</c>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&gt;&gt;", " ")
    text = re.sub(r"\[[^\]]+\]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []

    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    results: list[str] = []
    seen: set[str] = set()
    for part in parts:
        sentence = part.strip(" -")
        if len(sentence) < 35 or is_low_signal_text(sentence):
            continue
        normalized = normalize_text(sentence)
        if normalized in seen:
            continue
        seen.add(normalized)
        results.append(sentence)
    return results


def normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def is_low_signal_text(text: str) -> bool:
    lowered = normalize_text(text)
    if not lowered:
        return True
    if any(lowered.startswith(prefix) for prefix in LOW_SIGNAL_PREFIXES):
        return True
    words = lowered.split()
    if len(words) <= 3:
        return True
    repeated = sum(1 for idx in range(len(words) - 1) if words[idx] == words[idx + 1])
    return repeated >= max(2, len(words) // 3)


def infer_domain(context_text: str) -> str:
    lowered = context_text.lower()
    best_domain = "general"
    best_score = 0
    for domain, phrases in DOMAIN_RULES:
        score = sum(2 if phrase in lowered else 0 for phrase in phrases)
        if score > best_score:
            best_domain = domain
            best_score = score
    return best_domain


def extract_keywords(*, title: str, transcript_text: str, metadata: dict[str, Any], domain: str, limit: int = 6) -> list[str]:
    combined = build_context_text(title=title, transcript_text=transcript_text, metadata=metadata).lower()
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9\-]+", combined)
    counts: Counter[str] = Counter()

    title_tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9\-]+", title.lower())
    for token in title_tokens:
        normalized = normalize_keyword(token)
        if is_valid_keyword(normalized):
            counts[normalized] += 4

    download_metadata = metadata.get("download_metadata") or {}
    for token in download_metadata.get("tags") or []:
        normalized = normalize_keyword(token)
        if is_valid_keyword(normalized):
            counts[normalized] += 3

    for token in words:
        normalized = normalize_keyword(token)
        if is_valid_keyword(normalized):
            counts[normalized] += 1

    domain_preferred = {
        "gaming-goldmaking": ["wow", "gold", "token", "profession", "alt-army", "auctionator", "knowledge"],
        "agent-memory": ["memory", "dreaming", "wiki", "active-memory", "obsidian", "recall"],
        "ai-design": ["claude", "canva", "design", "poster", "gpt-image", "sub-agents"],
        "agent-video-analysis": ["claude", "video-analysis", "frames", "transcript", "mcp", "higgsfield-mcp"],
        "software-build": ["calendly", "claude-code", "source-code", "spec", "app", "setup"],
    }.get(domain, [])

    ordered: list[str] = []
    for token in domain_preferred:
        if counts[token] > 0 and token not in ordered:
            ordered.append(token)

    for token, _score in counts.most_common(limit * 4):
        if token not in ordered:
            ordered.append(token)
        if len(ordered) >= limit:
            break
    return ordered[:limit]


def normalize_keyword(token: str) -> str:
    token = token.strip().lower()
    token = token.replace(" ", "-")
    token = re.sub(r"[^a-z0-9\-]+", "", token)
    token = token.strip("-")
    return token


def is_valid_keyword(token: str) -> bool:
    if not token or token in STOPWORDS:
        return False
    if len(token) < 4 and token not in {"wow", "mcp"}:
        return False
    if token.isdigit():
        return False
    if token in {"actually", "going", "right", "here", "some", "make", "thing", "things", "video", "videos", "today", "really"}:
        return False
    return True


def infer_classification(*, title: str, transcript_text: str, metadata: dict[str, Any], domain: str) -> dict[str, str]:
    haystack = build_context_text(title=title, transcript_text=transcript_text, metadata=metadata).lower()
    title_lower = title.lower()

    scores = {name: score_keywords(haystack, phrases) for name, phrases in CLASSIFICATION_RULES.items()}
    if domain in {"gaming-goldmaking", "software-build", "ai-design"}:
        scores["tutorial"] += 2
    if domain == "agent-memory":
        scores["workflow"] += 1
        scores["reference"] += 1
    if any(token in title_lower for token in ["beginner", "beginners", "course", "how to", "guide"]):
        scores["tutorial"] += 2

    best_type = max(scores, key=scores.get)
    top_score = scores[best_type]
    ordered = sorted(scores.values(), reverse=True)
    runner_up = ordered[1] if len(ordered) > 1 else 0
    if top_score <= 1:
        confidence = "low"
    elif top_score - runner_up >= 2 or top_score >= 5:
        confidence = "high"
    else:
        confidence = "medium"
    return {"type": best_type, "confidence": confidence}


def score_keywords(haystack: str, phrases: list[str]) -> int:
    return sum(1 for phrase in phrases if phrase in haystack)


def detect_themes(cues: list[dict[str, Any]], context_text: str) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    haystack = context_text.lower()
    for name, patterns in THEME_LIBRARY:
        cue_match = find_first_matching_cue(cues, patterns)
        text_match = next((pattern for pattern in patterns if pattern in haystack), None)
        if cue_match or text_match:
            results.append(
                {
                    "name": name,
                    "timestamp": cue_match["timestamp"] if cue_match else "",
                    "text": cue_match["text"] if cue_match else text_match or "",
                }
            )
    return results


def find_first_matching_cue(cues: list[dict[str, Any]], patterns: list[str]) -> dict[str, Any] | None:
    lowered = [pattern.lower() for pattern in patterns]
    for cue in cues:
        text = cue["text"].lower()
        if any(pattern in text for pattern in lowered):
            return cue
    return None


def build_executive_summary(
    title: str,
    classification: dict[str, str],
    themes: list[dict[str, str]],
    sentences: list[str],
    domain: str,
) -> str:
    opener = choose_best_sentence(sentences, fallback=title)
    practical = choose_practical_sentence(sentences, fallback=opener)
    summary_lines = [
        f"- This looks like a **{classification['type']}** video focused on {SUMMARY_DOMAIN_LANGUAGE.get(domain, SUMMARY_DOMAIN_LANGUAGE['general'])}.",
        f"- Core premise: {trim_sentence(opener, 180)}",
    ]
    if themes:
        summary_lines.append("- Main topics: " + ", ".join(theme["name"] for theme in themes[:5]) + ".")
    if practical:
        summary_lines.append(f"- Practical value: {trim_sentence(practical, 180)}")
    return "\n".join(summary_lines)


def choose_best_sentence(sentences: list[str], fallback: str) -> str:
    if not sentences:
        return fallback
    ranked = sorted(sentences, key=sentence_priority, reverse=True)
    return ranked[0]


def choose_practical_sentence(sentences: list[str], fallback: str) -> str:
    practical_markers = [
        "show you how",
        "first thing",
        "primary focus",
        "set up",
        "save money",
        "enable",
        "worth",
        "profit",
        "check",
        "practical win",
    ]
    fallback_normalized = normalize_text(fallback)
    for sentence in sentences:
        lowered = sentence.lower()
        if normalize_text(sentence) == fallback_normalized and len(sentences) > 1:
            continue
        if any(marker in lowered for marker in practical_markers) and not is_low_signal_text(sentence):
            return sentence
    return fallback


def sentence_priority(sentence: str) -> tuple[int, int]:
    lowered = sentence.lower()
    score = 0
    for marker in ["show you how", "primary focus", "mental model", "how they fit", "i made", "i built", "profit", "worth", "focus"]:
        if marker in lowered:
            score += 2
    for penalty in ["subscribe", "community", "link below", "welcome back"]:
        if penalty in lowered:
            score -= 2
    return (score, len(sentence))


def build_classification_block(
    classification: dict[str, str], themes: list[dict[str, str]], keywords: list[str], domain: str
) -> str:
    theme_text = ", ".join(theme["name"] for theme in themes[:5]) or "pending-theme-detection"
    keyword_text = ", ".join(keywords) or "pending-keywords"
    return "\n".join(
        [
            f"- Type: {classification['type']}",
            f"- Confidence: {classification['confidence']}",
            f"- Domain: {domain}",
            f"- Themes: {theme_text}",
            f"- Keywords: {keyword_text}",
        ]
    )


def build_key_insights(sentences: list[str], themes: list[dict[str, str]]) -> str:
    bullets: list[str] = []
    seen: set[str] = set()

    for theme in themes:
        text = theme["text"]
        if text and not is_low_signal_text(text):
            bullet = trim_sentence(text, 170)
            normalized = normalize_text(bullet)
            if normalized and normalized not in seen:
                seen.add(normalized)
                bullets.append(f"- {bullet}")
        if len(bullets) >= 3:
            break

    preferred_patterns = [
        "show you how",
        "primary focus",
        "mental model",
        "what you can do",
        "first thing",
        "worth",
        "profit",
        "set up",
    ]
    for sentence in sorted(sentences, key=sentence_priority, reverse=True):
        lowered = sentence.lower()
        if any(pattern in lowered for pattern in preferred_patterns):
            normalized = normalize_text(sentence)
            if normalized not in seen:
                seen.add(normalized)
                bullets.append(f"- {trim_sentence(sentence, 170)}")
        if len(bullets) >= 5:
            break

    if not bullets:
        bullets = [f"- {trim_sentence(sentence, 170)}" for sentence in sentences[:4] if not is_low_signal_text(sentence)]
    return "\n".join(bullets[:5]) or "- Pending review"


def build_timestamped_notes(cues: list[dict[str, Any]], themes: list[dict[str, str]]) -> str:
    if not cues:
        fallback_notes = [f"- {theme['name'].title()}: {trim_sentence(theme['text'], 150)}" for theme in themes[:4] if theme["text"]]
        return "\n".join(fallback_notes) or "- Pending review"

    selected: list[dict[str, Any]] = []
    used_timestamps: set[str] = set()

    for theme in themes:
        if theme.get("timestamp") and theme["timestamp"] not in used_timestamps:
            cue = next((item for item in cues if item["timestamp"] == theme["timestamp"]), None)
            if cue and not is_low_signal_text(cue["text"]):
                selected.append(cue)
                used_timestamps.add(cue["timestamp"])
        if len(selected) >= 5:
            break

    if len(selected) < 4:
        indices = [0, len(cues) // 4, len(cues) // 2, (3 * len(cues)) // 4, len(cues) - 1]
        for idx in indices:
            if idx < 0 or idx >= len(cues):
                continue
            cue = cues[idx]
            if cue["timestamp"] in used_timestamps or is_low_signal_text(cue["text"]):
                continue
            selected.append(cue)
            used_timestamps.add(cue["timestamp"])
            if len(selected) >= 5:
                break

    selected.sort(key=lambda item: item["start_seconds"])
    lines = [f"- {cue['timestamp']} — {trim_sentence(cue['text'], 160)}" for cue in selected[:5]]
    return "\n".join(lines) or "- Pending review"


def build_reviewer_feedback(classification: dict[str, str], themes: list[dict[str, str]], domain: str) -> str:
    strengths: list[str] = []
    risks: list[str] = []
    theme_names = {theme["name"] for theme in themes}

    if "automation" in theme_names or "workflow" in theme_names:
        strengths.append("Shows a repeatable operating pattern rather than a one-off demo.")
    if "quality control" in theme_names:
        strengths.append("Includes some signal about review, quality, or constraints instead of pure hype.")
    if domain == "gaming-goldmaking":
        strengths.append("Useful for extracting repeatable market or profession routines.")
    if domain == "agent-memory":
        strengths.append("Useful for clarifying feature roles and enablement order.")

    if classification["type"] == "inspiration":
        risks.append("Claims may be more promotional than operationally neutral.")
    if "creator business" in theme_names:
        risks.append("Part of the content may be funnel or community promotion rather than core technique.")
    if domain == "gaming-goldmaking":
        risks.append("Realm prices, profession depth, and patch timing can make the exact numbers non-portable.")
    if domain == "software-build":
        risks.append("The setup path may rely on hidden local context unless tested on a clean machine.")

    strengths = strengths or ["Good practical demo structure with concrete examples."]
    risks = risks or ["Needs real-world validation before treating the workflow as production-ready."]

    return "\n".join(
        [
            "- Strengths:",
            *[f"  - {item}" for item in strengths[:3]],
            "- Risks / caveats:",
            *[f"  - {item}" for item in risks[:3]],
        ]
    )


def build_suggested_followups(classification: dict[str, str], themes: list[dict[str, str]], domain: str) -> str:
    followups = FOLLOWUP_LIBRARY.get(domain, []).copy()
    if not followups:
        followups = [
            "- Capture the strongest repeatable pattern from the video and save it as a reusable note or template.",
            "- Test the method once in a real workflow before trusting the headline claim.",
        ]

    theme_names = {theme["name"] for theme in themes}
    if "automation" in theme_names:
        followups.append("- Add a review checkpoint before scaling the method or delegating it fully.")
    if classification["type"] == "tutorial":
        followups.append("- Turn the workflow into a short SOP or agent skill with inputs, steps, and review gates.")
    return "\n".join(followups[:4])


def trim_sentence(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    trimmed = text[: limit - 3].rsplit(" ", 1)[0].strip()
    return f"{trimmed}..."
