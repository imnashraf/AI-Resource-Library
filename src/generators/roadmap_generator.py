"""Learning Roadmap Compiler (LEARNING_ROADMAP.md).

Generates prerequisite-ordered pedagogical learning tracks (Paths A through H)
guiding users from foundational concepts through capstone implementations.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from src.config import INVENTORY_DIR, LEARNING_ROADMAP_PATH

# 8 Curated Learning Tracks with 5 progressive milestones
ROADMAP_TRACKS = [
    {
        "path_id": "PATH A",
        "title": "Complete Beginner",
        "badge": "Beginner Track",
        "audience": "Newcomers seeking a structured, no-fluff path to personal AI fluency.",
        "description": "Starts with fundamental workspace configuration, builds daily conversational habits, masters token limits, earns official certifications, and culminates in a multi-system weekend build.",
        "stages": [
            {
                "stage": "START HERE",
                "id": "AI-001",
                "title": "The Ultimate Claude Starter Setup Guide",
                "difficulty": "Beginner",
                "why_here": "Establishes core account settings, project memory, and custom instructions before touching complex tools.",
                "key_takeaway": "Configuring memory and instructions once eliminates 80% of generic outputs forever.",
            },
            {
                "stage": "NEXT",
                "id": "AI-004",
                "title": "The Full Claude Dos and Don'ts",
                "difficulty": "Beginner to Advanced",
                "why_here": "Instills best practices and eliminates common mistakes before bad prompting habits solidify.",
                "key_takeaway": "Specific framing, negative constraints, and modular context yield professional results.",
            },
            {
                "stage": "INTERMEDIATE",
                "id": "AI-005",
                "title": "10 Ways to Stop Burning Your Claude Usage Limit",
                "difficulty": "Beginner",
                "why_here": "Prevents session interruptions by teaching smart context batching and model routing.",
                "key_takeaway": "Smarter prompting and prompt caching double your effective daily capacity without extra cost.",
            },
            {
                "stage": "ADVANCED",
                "id": "AI-056",
                "title": "13 Free AI Courses & Certifications",
                "difficulty": "Beginner",
                "why_here": "Solidifies self-taught skills with structured curricula and verifiable certificates from Anthropic, Google, and IBM.",
                "key_takeaway": "Industry credentials provide confidence and external validation of your capabilities.",
            },
            {
                "stage": "CAPSTONE PROJECT",
                "id": "AI-059",
                "title": "The Weekend AI Systems Guide",
                "difficulty": "Beginner",
                "why_here": "Applies all foundational concepts into building 8 real, functioning systems in two days.",
                "key_takeaway": "Build proposal generators, competitor watches, and copy auditors running without code.",
            },
        ],
    },
    {
        "path_id": "PATH B",
        "title": "AI Power User",
        "badge": "Power User Track",
        "audience": "Professionals wanting to squeeze maximum daily productivity out of Claude and desktop tools.",
        "description": "Expands your desktop toolkit, refines context engineering, automates scheduled routines, integrates Excel Copilot, and constructs a continuous AI second brain.",
        "stages": [
            {
                "stage": "START HERE",
                "id": "AI-003",
                "title": "The Ultimate Claude Toolkit",
                "difficulty": "Beginner",
                "why_here": "Assembles the essential ecosystem of desktop apps, browser extensions, and community skills.",
                "key_takeaway": "The right companion utilities multiply the raw model's efficiency across daily workflows.",
            },
            {
                "stage": "NEXT",
                "id": "AI-061",
                "title": "33 Best Claude Prompts: Refreshed for Sonnet 5",
                "difficulty": "Beginner to Advanced",
                "why_here": "Transitions your prompting approach from basic questions to structured context engineering.",
                "key_takeaway": "Battle-tested templates for coding, data, strategy, and team decisions.",
            },
            {
                "stage": "INTERMEDIATE",
                "id": "AI-007",
                "title": "Claude Routines Setup Guide",
                "difficulty": "Intermediate",
                "why_here": "Moves beyond interactive chat into scheduled automations that execute on autopilot.",
                "key_takeaway": "Scheduled routines perform recurring operational tasks even when you are away from your desk.",
            },
            {
                "stage": "ADVANCED",
                "id": "AI-064",
                "title": "Copilot in Excel: The Prompts I Use Every Week",
                "difficulty": "Beginner",
                "why_here": "Integrates LLM reasoning with commercial spreadsheets for automated health-checks and forecasting.",
                "key_takeaway": "Plain-English spreadsheet queries replace fragile nested formulas for executive reporting.",
            },
            {
                "stage": "CAPSTONE PROJECT",
                "id": "AI-068",
                "title": "4 Ways To Get Ahead Of Everyone Else Using AI",
                "difficulty": "Intermediate",
                "why_here": "Brings together an AI second brain, chained workflows, and specialized teammates.",
                "key_takeaway": "A completely integrated personal intelligence operating system.",
            },
        ],
    },
    {
        "path_id": "PATH C",
        "title": "Claude Code Specialist",
        "badge": "CLI & Agent Track",
        "audience": "Developers and technical creators building software inside the terminal with Claude Code.",
        "description": "Covers initial CLI setup, commands mastery, agent taxonomy, loop engineering, and automated verification guardrails.",
        "stages": [
            {
                "stage": "START HERE",
                "id": "AI-008",
                "title": "Claude Code 10x Setup Guide",
                "difficulty": "Intermediate",
                "why_here": "Configures CLAUDE.md, permissions, hooks, and MCP servers for reliable agentic coding.",
                "key_takeaway": "A rigorous CLAUDE.md configuration transforms unpredictable AI into a predictable pair programmer.",
            },
            {
                "stage": "NEXT",
                "id": "AI-010",
                "title": "Claude Code Commands Guide",
                "difficulty": "Intermediate",
                "why_here": "Mastering CLI shortcuts, sub-commands, and terminal flags for high-velocity navigation.",
                "key_takeaway": "Fluency in slash commands and keyboard shortcuts cuts terminal cognitive friction by half.",
            },
            {
                "stage": "INTERMEDIATE",
                "id": "AI-009",
                "title": "7 Claude Code Agent Types",
                "difficulty": "Intermediate",
                "why_here": "Provides a conceptual taxonomy of agent architectures and when to deploy each one.",
                "key_takeaway": "Selecting the right agent topology prevents runaway loops and context contamination.",
            },
            {
                "stage": "ADVANCED",
                "id": "AI-050",
                "title": "Loop Engineering",
                "difficulty": "Advanced",
                "why_here": "Combines automations, worktrees, skills, and subagents into long-running loops.",
                "key_takeaway": "Shift from prompting individual steps to orchestrating self-correcting development loops.",
            },
            {
                "stage": "CAPSTONE PROJECT",
                "id": "AI-071",
                "title": "The 5 Checks: Full Verification Guide",
                "difficulty": "Intermediate",
                "why_here": "Enforces automated test, regression, and diff checks before code is considered complete.",
                "key_takeaway": "Eliminates premature task completion by enforcing rigorous verification gates.",
            },
        ],
    },
    {
        "path_id": "PATH D",
        "title": "AI Automation Engineer",
        "badge": "Automation Track",
        "audience": "Operators and builders automating business processes, web data extraction, and pipelines.",
        "description": "Begins with voice and browser automation, tackles weekly recurring processes, expands to 10 automated routines, connects scrapers, and builds an autonomous competitor intelligence engine.",
        "stages": [
            {
                "stage": "START HERE",
                "id": "AI-006",
                "title": "Claude, Wispr Flow & Cookiy AI Setup Guide",
                "difficulty": "Beginner",
                "why_here": "Connects voice transcription directly to browser actions for rapid execution.",
                "key_takeaway": "Speaking your intent directly into browser automation saves hours of manual point-and-click.",
            },
            {
                "stage": "NEXT",
                "id": "AI-035",
                "title": "The 3 Business Processes You Can Automate This Week",
                "difficulty": "Beginner",
                "why_here": "Immediate operational wins: automated lead follow-up, meeting synthesis, and weekly digests.",
                "key_takeaway": "Reclaim 11–15 hours weekly by setting up automated Gmail and calendar routines.",
            },
            {
                "stage": "INTERMEDIATE",
                "id": "AI-062",
                "title": "10 AI Automations That Run Your Week",
                "difficulty": "Intermediate",
                "why_here": "Expands scheduled routines across triage, briefings, expense categorization, and recaps.",
                "key_takeaway": "A cohesive weekly automation schedule keeps operations disciplined without manual oversight.",
            },
            {
                "stage": "ADVANCED",
                "id": "AI-063",
                "title": "How to Scrape Thousands of Leads with Claude",
                "difficulty": "Intermediate",
                "why_here": "Integrates ScrapeGraphAI with Claude connectors to extract structured public contact lists.",
                "key_takeaway": "Scheduled web scrapers feed clean business data directly into spreadsheet databases.",
            },
            {
                "stage": "CAPSTONE PROJECT",
                "id": "AI-043",
                "title": "The Competitor Intelligence Engine",
                "difficulty": "Advanced",
                "why_here": "End-to-end production architecture: scheduled competitor scraping, gap analysis, and n8n workflows.",
                "key_takeaway": "A commercial-grade market intelligence pipeline delivered directly into client channels.",
            },
        ],
    },
    {
        "path_id": "PATH E",
        "title": "AI Agency & Freelancer",
        "badge": "Agency Track",
        "audience": "Freelancers and consultants selling AI implementations, client workflows, and retainers.",
        "description": "Guides the journey from zero client proof through packaging sellable services, cold outreach sequences, high-value boring automations, and enterprise agent management.",
        "stages": [
            {
                "stage": "START HERE",
                "id": "AI-034",
                "title": "From Zero to Warm Inbound: How to Get Clients With AI Skills",
                "difficulty": "Beginner",
                "why_here": "Establishes the foundational strategy from initial free proof projects to warm inbound referrals.",
                "key_takeaway": "Clear pricing ladders and social proof assets eliminate dependence on cold outreach.",
            },
            {
                "stage": "NEXT",
                "id": "AI-038",
                "title": "5 AI Services You Can Sell This Week",
                "difficulty": "Beginner",
                "why_here": "Focuses on 5 non-coding offerings (copy, content repurposing, chatbots, outbound, vibe-design).",
                "key_takeaway": "Immediate revenue generation using accessible tools with predefined scopes of work.",
            },
            {
                "stage": "INTERMEDIATE",
                "id": "AI-037",
                "title": "The Cold Outreach Playbook",
                "difficulty": "Intermediate",
                "why_here": "Standardizes cold outreach anatomy, 4-step follow-ups, and proof assets that convert calls.",
                "key_takeaway": "Targeting ideal client profiles with personalized proof dramatically increases booked meetings.",
            },
            {
                "stage": "ADVANCED",
                "id": "AI-040",
                "title": "The 7 Boring Automations",
                "difficulty": "Intermediate",
                "why_here": "Teaches seven reliable, recurring automations that dental, legal, and accounting firms gladly pay for.",
                "key_takeaway": "Boring back-office automations generate stable monthly recurring revenue (MRR).",
            },
            {
                "stage": "CAPSTONE PROJECT",
                "id": "AI-058",
                "title": "The Agent Manager Build Guide",
                "difficulty": "Intermediate",
                "why_here": "Creates a proof-of-work scorecard and a 3-agent team with hard human approval gates.",
                "key_takeaway": "Demonstrates to enterprise clients that you can deploy and govern multi-agent teams safely.",
            },
        ],
    },
    {
        "path_id": "PATH F",
        "title": "AI Startup Builder",
        "badge": "Startup Track",
        "audience": "Solo founders and entrepreneurs building micro-SaaS, digital products, and MVPs.",
        "description": "Pressure-tests ideas with an AI cofounder, deploys a $20/month lean toolstack, architects full startup infrastructure, prevents pre-launch bugs, and packages sellable digital assets.",
        "stages": [
            {
                "stage": "START HERE",
                "id": "AI-042",
                "title": "Your Brutally Honest AI Cofounder",
                "difficulty": "Beginner",
                "why_here": "Applies Sam Altman's startup playbook to score product ideas and expose hidden failure modes.",
                "key_takeaway": "Rigorous early validation prevents building products that nobody wants.",
            },
            {
                "stage": "NEXT",
                "id": "AI-057",
                "title": "The $20/Month Startup Stack",
                "difficulty": "Intermediate",
                "why_here": "Assembles a battle-tested 13-tool stack for domains, auth, database, payments, and search.",
                "key_takeaway": "Run a lean, high-velocity software company on minimal initial capital expenditure.",
            },
            {
                "stage": "INTERMEDIATE",
                "id": "AI-032",
                "title": "The Startup Stack",
                "difficulty": "Intermediate",
                "why_here": "Coordinates idea validation, build tools, launch checklists, and initial user acquisition.",
                "key_takeaway": "A synchronized blueprint for building software with Claude from day one to launch.",
            },
            {
                "stage": "ADVANCED",
                "id": "AI-039",
                "title": "5 Things That Will Break Your Claude Code App Before Launch",
                "difficulty": "Intermediate",
                "why_here": "Fixes launch-critical bugs: error boundaries, Sentry logging, resilient forms, and 404 pages.",
                "key_takeaway": "Hardening your frontend and error states protects early user trust and retention.",
            },
            {
                "stage": "CAPSTONE PROJECT",
                "id": "AI-045",
                "title": "Build a Digital Product With Claude + Canva",
                "difficulty": "Beginner",
                "why_here": "End-to-end digital product generation, template formatting, and commercial release.",
                "key_takeaway": "Rapidly design, package, and monetize downloadable assets with zero design overhead.",
            },
        ],
    },
    {
        "path_id": "PATH G",
        "title": "AI Developer",
        "badge": "Developer Track",
        "audience": "Software engineers and architects integrating multi-model APIs, frameworks, and agent orchestration.",
        "description": "Integrates Claude Code with Codex, runs multi-model reviews, builds unified teams with Gemini CLI, configures Ruflo agent frameworks, and establishes an LLM peer-review council.",
        "stages": [
            {
                "stage": "START HERE",
                "id": "AI-011",
                "title": "Claude Code Codex Setup Guide",
                "difficulty": "Advanced",
                "why_here": "Bridges Claude Code with OpenAI Codex in the same workspace.",
                "key_takeaway": "Dual-model availability provides specialized code generation and alternative problem-solving angles.",
            },
            {
                "stage": "NEXT",
                "id": "AI-054",
                "title": "Claude Opus vs ChatGPT 5.5: Stop Debating. Run Both",
                "difficulty": "Intermediate",
                "why_here": "Establishes real-time automated code reviews where Codex inspects Claude's output.",
                "key_takeaway": "Cross-model code review catches subtle edge cases and logic bugs before deployment.",
            },
            {
                "stage": "INTERMEDIATE",
                "id": "AI-055",
                "title": "Run Claude Code, ChatGPT & Gemini As One AI Team",
                "difficulty": "Advanced",
                "why_here": "Coordinates Claude (builder), Codex (reviewer), and Gemini (large-context file processor).",
                "key_takeaway": "Leverage model specialization without incurring additional subscription costs.",
            },
            {
                "stage": "ADVANCED",
                "id": "AI-014",
                "title": "Ruflo Multi-Agent Framework Setup Guide",
                "difficulty": "Advanced",
                "why_here": "Sets up Ruflo to coordinate parallel agents with shared state and production pipelines.",
                "key_takeaway": "Multi-agent orchestration transforms linear tasks into parallel, high-throughput execution.",
            },
            {
                "stage": "CAPSTONE PROJECT",
                "id": "AI-029",
                "title": "The LLM Council Setup Guide",
                "difficulty": "Advanced",
                "why_here": "Multi-model debate council where diverse architectures critique and refine complex deliverables.",
                "key_takeaway": "Collective model reasoning produces superior architectural decisions and robust software.",
            },
        ],
    },
    {
        "path_id": "PATH H",
        "title": "AI Business & Monetisation",
        "badge": "Executive Track",
        "audience": "Business leaders, content creators, and growth marketers scaling distribution and revenue.",
        "description": "Builds data-backed content pillars, crafts human-looking visual assets, reverse-engineers viral competitors, automates paid Meta ads teams, and executes precision lead generation with Apollo.",
        "stages": [
            {
                "stage": "START HERE",
                "id": "AI-036",
                "title": "The Creator Tracking System",
                "difficulty": "Intermediate",
                "why_here": "Establishes data-driven content tracking across reach, authority, and conversion pillars.",
                "key_takeaway": "Systematic tracking eliminates guesswork and surfaces outlier content patterns.",
            },
            {
                "stage": "NEXT",
                "id": "AI-047",
                "title": "Carousels That Don't Look AI-Generated",
                "difficulty": "Intermediate",
                "why_here": "Master visual design prompts that kill generic AI artifacts and build strong personal brand authority.",
                "key_takeaway": "Designer-grade visual carousels significantly increase social engagement and bookmark rates.",
            },
            {
                "stage": "INTERMEDIATE",
                "id": "AI-048",
                "title": "The Sandcastles Content Strategy Setup Guide",
                "difficulty": "Intermediate",
                "why_here": "Reverse-engineers top competitor content patterns to construct data-backed content playbooks.",
                "key_takeaway": "Extracting proven market signals accelerates growth without blind trial-and-error.",
            },
            {
                "stage": "ADVANCED",
                "id": "AI-051",
                "title": "Run Your Meta Ads Team Inside Claude",
                "difficulty": "Advanced",
                "why_here": "Builds an in-house ads team using MCP connectors for competitor ad spying and creative scoring.",
                "key_takeaway": "Automate ad intelligence and campaign management directly inside conversation.",
            },
            {
                "stage": "CAPSTONE PROJECT",
                "id": "AI-052",
                "title": "The Apollo Lead List Playbook",
                "difficulty": "Intermediate",
                "why_here": "Executes filter-stacked, trigger-based B2B lead generation scaling past standard platform limits.",
                "key_takeaway": "Build high-converting outbound pipelines with rigorous list hygiene and lookalike targeting.",
            },
        ],
    },
]


TRACK_DURATIONS = {
    "PATH A": ("2–3 weeks (15–20 hours total)", ["2–3 hours", "2–3 hours", "3–4 hours", "4–6 hours", "6–8 hours"]),
    "PATH B": ("3–4 weeks (20–25 hours total)", ["2–3 hours", "3–4 hours", "4–5 hours", "3–4 hours", "6–8 hours"]),
    "PATH C": ("4–5 weeks (30–40 hours total)", ["4–6 hours", "3–5 hours", "4–6 hours", "8–10 hours", "6–8 hours"]),
    "PATH D": ("4–6 weeks (35–45 hours total)", ["3–4 hours", "3–5 hours", "5–7 hours", "6–8 hours", "10–14 hours"]),
    "PATH E": ("4–6 weeks (30–40 hours total)", ["3–5 hours", "4–6 hours", "5–7 hours", "6–8 hours", "10–12 hours"]),
    "PATH F": ("4–6 weeks (35–50 hours total)", ["3–5 hours", "4–6 hours", "6–8 hours", "6–8 hours", "12–16 hours"]),
    "PATH G": ("5–7 weeks (40–55 hours total)", ["4–6 hours", "4–6 hours", "6–8 hours", "10–14 hours", "12–16 hours"]),
    "PATH H": ("3–5 weeks (25–35 hours total)", ["3–5 hours", "4–6 hours", "4–6 hours", "6–8 hours", "6–8 hours"]),
}


class LearningRoadmapGenerator:
    """Generates the publication-grade LEARNING_ROADMAP.md file."""

    def __init__(self, inventory_path: Path = None, output_path: Path = None):
        self.inventory_path = inventory_path or (INVENTORY_DIR / "master_inventory.json")
        self.output_path = output_path or LEARNING_ROADMAP_PATH

    def generate_markdown(self) -> str:
        """Construct the complete structured Markdown roadmap document."""
        lines = [
            "# AI Resource Library — Systematic Learning Roadmaps",
            "",
            "> **Prerequisite-Ordered Curricula Across 8 Professional Specializations**  ",
            "> **Reference Index:** [`MASTER_INDEX.md`](./MASTER_INDEX.md)  ",
            "> **Progression Standard:** Strictly follows the 5-stage milestone architecture:  ",
            "> $$\\text{START HERE} \\longrightarrow \\text{NEXT} \\longrightarrow \\text{INTERMEDIATE} \\longrightarrow \\text{ADVANCED} \\longrightarrow \\text{CAPSTONE PROJECT}$$  ",
            "",
            "---",
            "",
            "## Table of Contents",
            "",
        ]

        for track in ROADMAP_TRACKS:
            pid = track["path_id"]
            title = track["title"]
            anchor = f"{pid.lower().replace(' ', '-')}-{title.lower().replace(' ', '-').replace('&', '').replace('/', '')}"
            lines.append(f"- [{pid}: {title}](#{anchor}) — *{track['badge']}*")

        lines.append("- [Master Multi-Path Prerequisite Matrix](#master-multi-path-prerequisite-matrix)")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Render each track
        for track in ROADMAP_TRACKS:
            pid = track["path_id"]
            title = track["title"]
            badge = track["badge"]
            desc = track["description"]
            aud = track["audience"]
            track_dur, stage_durs = TRACK_DURATIONS.get(pid, ("3–4 weeks (20–30 hours total)", ["3–4 hours"] * 5))

            lines.append(f"## {pid}: {title}")
            lines.append(f"**Target Focus:** `{badge}` | **Ideal Audience:** {aud} | **Estimated Duration:** `{track_dur}`")
            lines.append("")
            lines.append(f"> {desc}")
            lines.append("")
            lines.append("### Progression Flow")
            lines.append("```")
            lines.append("┌─────────────────┐      ┌───────────────┐      ┌─────────────────┐      ┌────────────────┐      ┌────────────────────┐")
            lines.append("│ 1. START HERE   │ ───> │ 2. NEXT       │ ───> │ 3. INTERMEDIATE │ ───> │ 4. ADVANCED    │ ───> │ 5. CAPSTONE PROJECT│")
            lines.append("└─────────────────┘      └───────────────┘      └─────────────────┘      └────────────────┘      └────────────────────┘")
            lines.append("```")
            lines.append("")

            # Milestone Table
            lines.append("| Milestone Stage | Resource ID | Resource Title | Difficulty | Est. Time | Key Takeaway | Summary Link |")
            lines.append("|---|---|---|---|---|---|---|")

            for idx, s in enumerate(track["stages"]):
                stage_name = s["stage"]
                res_id = s["id"]
                res_title = s["title"]
                diff = s["difficulty"]
                takeaway = s["key_takeaway"]
                est_time = stage_durs[idx] if idx < len(stage_durs) else "3–4 hours"
                summary_link = f"[Read Summary](summaries/{res_id}.md)"
                lines.append(f"| **{stage_name}** | `{res_id}` | **{res_title}** | `{diff}` | {est_time} | {takeaway} | {summary_link} |")

            lines.append("")

            # In-depth Milestone Breakdown
            lines.append("### Detailed Milestone Breakdown")
            lines.append("")

            for idx, s in enumerate(track["stages"], 1):
                stage_name = s["stage"]
                res_id = s["id"]
                res_title = s["title"]
                why = s["why_here"]
                takeaway = s["key_takeaway"]
                est_time = stage_durs[idx - 1] if (idx - 1) < len(stage_durs) else "3–4 hours"

                lines.append(f"#### Step {idx}: {stage_name} — [{res_id}] {res_title}")
                lines.append(f"- **Difficulty Rating:** `{s['difficulty']}`")
                lines.append(f"- **Estimated Time:** `{est_time}`")
                lines.append(f"- **Why Positioned Here (Progression Rationale):** {why}")
                lines.append(f"- **Core Practical Takeaway:** {takeaway}")
                lines.append(f"- **Access:** [Structured Analytical Summary](summaries/{res_id}.md)")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Master Matrix Table
        lines.append("## Master Multi-Path Prerequisite Matrix")
        lines.append("")
        lines.append("Quickly cross-reference where core resources appear across tracks:")
        lines.append("")
        lines.append("| Track | 1. START HERE | 2. NEXT | 3. INTERMEDIATE | 4. ADVANCED | 5. CAPSTONE PROJECT |")
        lines.append("|---|---|---|---|---|---|")

        for track in ROADMAP_TRACKS:
            pid = track["path_id"]
            title = track["title"]
            st = track["stages"]
            lines.append(
                f"| **{pid}: {title}** | `{st[0]['id']}` {st[0]['title'][:20]}... | `{st[1]['id']}` {st[1]['title'][:20]}... | `{st[2]['id']}` {st[2]['title'][:20]}... | `{st[3]['id']}` {st[3]['title'][:20]}... | `{st[4]['id']}` {st[4]['title'][:20]}... |"
            )

        lines.append("")
        return "\n".join(lines)

    def write_file(self) -> Path:
        """Generate markdown and write to LEARNING_ROADMAP.md."""
        content = self.generate_markdown()
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(content, encoding="utf-8")
        return self.output_path
