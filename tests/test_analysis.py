from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from analysis import analyze_transcript, parse_vtt_cues


def test_parse_vtt_cues_deduplicates_and_extracts_timestamps(tmp_path):
    vtt_path = tmp_path / "sample.vtt"
    vtt_path.write_text(
        """WEBVTT
Kind: captions
Language: en

00:00:00.000 --> 00:00:02.000
Hello<00:00:00.500><c> world</c>

00:00:02.000 --> 00:00:04.000
Hello world

00:00:04.000 --> 00:00:06.000
Now we test setup and prompts.
""",
        encoding="utf-8",
    )

    cues = parse_vtt_cues(vtt_path)
    assert len(cues) == 2
    assert cues[0]["timestamp"] == "00:00:00"
    assert cues[0]["text"] == "Hello world"
    assert cues[1]["timestamp"] == "00:00:04"


def test_analyze_transcript_generates_first_pass_sections(tmp_path):
    vtt_path = tmp_path / "sample.vtt"
    vtt_path.write_text(
        """WEBVTT

00:00:00.000 --> 00:00:04.000
In this beginners course, I'll show you how to set up Claude and generate posters.

00:00:20.000 --> 00:00:24.000
You can ask Claude to propose three styles from the brief.

00:01:00.000 --> 00:01:04.000
Spawn sub-agents to do the design work in parallel.

00:02:00.000 --> 00:02:04.000
Use Canva Magic Layers to edit text and layout.

00:03:00.000 --> 00:03:04.000
Then adapt the reference design in bulk across a whole client roster.
""",
        encoding="utf-8",
    )

    transcript_text = "\n".join(
        [
            "In this beginners course, I'll show you how to set up Claude and generate posters.",
            "You can ask Claude to propose three styles from the brief.",
            "Spawn sub-agents to do the design work in parallel.",
            "Use Canva Magic Layers to edit text and layout.",
            "Then adapt the reference design in bulk across a whole client roster.",
        ]
    )

    analysis = analyze_transcript(
        title="Claude + Canva = Design on Autopilot (Beginners Course)",
        transcript_text=transcript_text,
        transcript_vtt_path=vtt_path,
        metadata={
            "download_metadata": {
                "tags": ["Claude", "Canva", "design", "poster"],
                "categories": ["Education"],
            }
        },
    )

    assert analysis["classification"]["type"] == "tutorial"
    assert "setup" in analysis["classification_block"]
    assert "Domain: ai-design" in analysis["classification_block"]
    assert "Claude" in analysis["executive_summary"]
    assert "00:00:00" in analysis["timestamped_notes"]
    assert "Canva" in analysis["timestamped_notes"] or "Magic Layers" in analysis["timestamped_notes"]
    assert "QA step" in analysis["suggested_followups"] or "review checkpoint" in analysis["suggested_followups"]


def test_analyze_transcript_detects_memory_domain_and_non_design_summary(tmp_path):
    vtt_path = tmp_path / "memory.vtt"
    vtt_path.write_text(
        """WEBVTT

00:00:00.000 --> 00:00:04.000
Three updates just dropped that completely change how your agent stores, organizes, and recalls information.

00:00:30.000 --> 00:00:34.000
Your agent's memory now has three distinct jobs: keeping long-term memory, organizing it, and recalling it.

00:01:00.000 --> 00:01:05.000
Dreaming, memory wiki, and active memory each do different parts of that pipeline.
""",
        encoding="utf-8",
    )

    transcript_text = "\n".join(
        [
            "Three updates just dropped that completely change how your agent stores, organizes, and recalls information.",
            "Your agent's memory now has three distinct jobs: keeping long-term memory, organizing it, and recalling it.",
            "Dreaming, memory wiki, and active memory each do different parts of that pipeline.",
        ]
    )

    analysis = analyze_transcript(
        title="OpenClaw's New Memory System Is Crazy",
        transcript_text=transcript_text,
        transcript_vtt_path=vtt_path,
        metadata={
            "download_metadata": {
                "tags": ["openclaw memory", "dreaming", "memory wiki", "obsidian"],
                "categories": ["Science & Technology"],
            }
        },
    )

    assert analysis["domain"] == "agent-memory"
    assert "memory architecture" in analysis["executive_summary"]
    assert "design workflow" not in analysis["executive_summary"]
    assert any(keyword in analysis["keywords"] for keyword in ["memory", "dreaming", "wiki"])


def test_analyze_transcript_extracts_domain_keywords_for_wow_goldmaking(tmp_path):
    vtt_path = tmp_path / "wow.vtt"
    vtt_path.write_text(
        """WEBVTT

00:00:00.000 --> 00:00:04.000
I'm going to show you how I made an entire WoW token in two hours with my alt army.

00:05:00.000 --> 00:05:04.000
My primary focus is multicrafting alloys, enchanting, and staying on top of profession knowledge.

00:10:00.000 --> 00:10:05.000
The patron orders and auction house pricing are the repeatable profit engine.
""",
        encoding="utf-8",
    )

    transcript_text = "\n".join(
        [
            "I'm going to show you how I made an entire WoW token in two hours with my alt army.",
            "My primary focus is multicrafting alloys, enchanting, and staying on top of profession knowledge.",
            "The patron orders and auction house pricing are the repeatable profit engine.",
        ]
    )

    analysis = analyze_transcript(
        title="Quick WoW Token without leaving Silvermoon! - Profession Alt Army",
        transcript_text=transcript_text,
        transcript_vtt_path=vtt_path,
        metadata={
            "download_metadata": {
                "tags": ["WoW", "Profession", "Gold", "Enchanting", "Auctionator"],
                "categories": ["Gaming"],
            }
        },
    )

    assert analysis["domain"] == "gaming-goldmaking"
    assert "World of Warcraft" in analysis["executive_summary"]
    assert any(keyword in analysis["keywords"] for keyword in ["wow", "gold", "profession", "auctionator"])
    assert "going" not in analysis["keywords"]


def test_analyze_transcript_filters_promo_cta_from_insights(tmp_path):
    vtt_path = tmp_path / "promo.vtt"
    vtt_path.write_text(
        """WEBVTT

00:00:00.000 --> 00:00:04.000
Join my free community below for the template and source code.

00:00:10.000 --> 00:00:15.000
I'll show you how to turn a video into frames, transcript notes, and a reusable Claude workflow.

00:00:20.000 --> 00:00:25.000
The useful part is extracting timestamps and frames so the agent can reason over the clip.
""",
        encoding="utf-8",
    )

    transcript_text = "\n".join(
        [
            "Join my free community below for the template and source code.",
            "I'll show you how to turn a video into frames, transcript notes, and a reusable Claude workflow.",
            "The useful part is extracting timestamps and frames so the agent can reason over the clip.",
        ]
    )

    analysis = analyze_transcript(
        title="My Claude Code Can INSTANTLY Watch Any Video (Here's How)",
        transcript_text=transcript_text,
        transcript_vtt_path=vtt_path,
        metadata={
            "download_metadata": {
                "tags": ["Claude Code", "video", "frames"],
                "categories": ["Science & Technology"],
            }
        },
    )

    assert "free community" not in analysis["key_insights"].lower()
    assert "source code" not in analysis["timestamped_notes"].lower()


def test_analyze_transcript_prefers_video_agent_domain_for_watch_any_video(tmp_path):
    vtt_path = tmp_path / "video-agent.vtt"
    vtt_path.write_text(
        """WEBVTT

00:00:00.000 --> 00:00:05.000
I'll show you how my Claude Code setup watches any YouTube video, extracts frames, and reads the transcript.

00:00:20.000 --> 00:00:25.000
The workflow sends frame context and transcript chunks back to the agent for analysis.

00:00:45.000 --> 00:00:50.000
This is better for video research than treating it like a generic coding repo demo.
""",
        encoding="utf-8",
    )

    transcript_text = "\n".join(
        [
            "I'll show you how my Claude Code setup watches any YouTube video, extracts frames, and reads the transcript.",
            "The workflow sends frame context and transcript chunks back to the agent for analysis.",
            "This is better for video research than treating it like a generic coding repo demo.",
        ]
    )

    analysis = analyze_transcript(
        title="My Claude Code Can INSTANTLY Watch Any Video (Here's How)",
        transcript_text=transcript_text,
        transcript_vtt_path=vtt_path,
        metadata={
            "download_metadata": {
                "tags": ["Claude Code", "video analysis", "frames", "transcript"],
                "categories": ["Science & Technology"],
            }
        },
    )

    assert analysis["domain"] == "agent-video-analysis"
    assert "video analysis" in analysis["executive_summary"].lower()


def test_analyze_transcript_promotes_specific_keywords_over_generic_fillers(tmp_path):
    vtt_path = tmp_path / "keywords.vtt"
    vtt_path.write_text(
        """WEBVTT

00:00:00.000 --> 00:00:05.000
This Claude Code workflow uses Higgsfield MCP to turn frames and captions into video analysis.

00:00:10.000 --> 00:00:15.000
It actually works because the MCP passes structured frame data and transcript context.

00:00:20.000 --> 00:00:25.000
The useful output is frame analysis, transcript notes, and reusable prompts.
""",
        encoding="utf-8",
    )

    transcript_text = "\n".join(
        [
            "This Claude Code workflow uses Higgsfield MCP to turn frames and captions into video analysis.",
            "It actually works because the MCP passes structured frame data and transcript context.",
            "The useful output is frame analysis, transcript notes, and reusable prompts.",
        ]
    )

    analysis = analyze_transcript(
        title="Claude Code + Higgsfield MCP = Content MACHINE",
        transcript_text=transcript_text,
        transcript_vtt_path=vtt_path,
        metadata={
            "download_metadata": {
                "tags": ["Claude Code", "Higgsfield MCP", "video analysis", "frames"],
                "categories": ["Science & Technology"],
            }
        },
    )

    assert "higgsfield-mcp" in analysis["keywords"] or "higgsfield" in analysis["keywords"]
    assert "mcp" in analysis["keywords"]
    assert "actually" not in analysis["keywords"]


def test_analyze_transcript_uses_distinct_practical_sentence_when_available(tmp_path):
    vtt_path = tmp_path / "summary.vtt"
    vtt_path.write_text(
        """WEBVTT

00:00:00.000 --> 00:00:05.000
I'll show you how to use Claude Code to watch any video and pull out transcript context.

00:00:12.000 --> 00:00:18.000
The practical win is that you can isolate frames, timestamps, and prompt-ready notes before handing the task back to the agent.

00:00:30.000 --> 00:00:35.000
That makes the workflow more useful than a generic transcript-only summary.
""",
        encoding="utf-8",
    )

    transcript_text = "\n".join(
        [
            "I'll show you how to use Claude Code to watch any video and pull out transcript context.",
            "The practical win is that you can isolate frames, timestamps, and prompt-ready notes before handing the task back to the agent.",
            "That makes the workflow more useful than a generic transcript-only summary.",
        ]
    )

    analysis = analyze_transcript(
        title="My Claude Code Can INSTANTLY Watch Any Video (Here's How)",
        transcript_text=transcript_text,
        transcript_vtt_path=vtt_path,
        metadata={
            "download_metadata": {
                "tags": ["Claude Code", "video analysis", "frames", "transcript"],
                "categories": ["Science & Technology"],
            }
        },
    )

    assert "Core premise: I'll show you how to use Claude Code to watch any video" in analysis["executive_summary"]
    assert "Practical value: The practical win is that you can isolate frames, timestamps, and prompt-ready notes" in analysis["executive_summary"]
