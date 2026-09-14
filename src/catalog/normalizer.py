"""Normalization rules, taxonomy mapping, and CSV injection defenses."""

import re
from typing import Dict, Any, List
from src.catalog.models import DifficultyLevel, ContentStatus, ResourceRecord


def sanitize_csv_value(val: Any) -> Any:
    """Defend against CSV/formula injection in spreadsheet applications."""
    if isinstance(val, str):
        # If string starts with dangerous formula symbols =, +, -, @
        if val.startswith(("=", "+", "-", "@")):
            return "'" + val
    return val


def normalize_difficulty(raw_diff: str) -> DifficultyLevel:
    """Normalize raw difficulty string to DifficultyLevel enum."""
    clean = raw_diff.strip().lower()
    if "beginner to advanced" in clean or "all levels" in clean:
        return DifficultyLevel.ALL_LEVELS
    elif "beginner" in clean:
        return DifficultyLevel.BEGINNER
    elif "advanced" in clean:
        return DifficultyLevel.ADVANCED
    elif "intermediate" in clean:
        return DifficultyLevel.INTERMEDIATE
    return DifficultyLevel.ALL_LEVELS


def derive_subcategory(category: str, slug: str, title: str) -> str:
    """Derive descriptive subcategory from title and slug context."""
    s = f"{slug} {title}".lower()

    if category == "Claude Code":
        if any(w in s for w in ["agent", "multi-agent", "ruflo"]):
            return "Agent Architecture"
        elif any(w in s for w in ["setup", "install", "config", "stack"]):
            return "Environment Setup"
        elif any(w in s for w in ["command", "shortcut", "cli", "flags"]):
            return "CLI Commands"
        elif any(w in s for w in ["plugin", "codex", "gemini", "ollama"]):
            return "Model & Tool Interop"
        elif any(w in s for w in ["test", "check", "verify", "break"]):
            return "Testing & Reliability"
        return "CLI Workflows"

    elif category == "Getting Started":
        if any(w in s for w in ["routine", "limit", "token", "burn"]):
            return "Usage & Optimization"
        elif any(w in s for w in ["course", "certification", "learn"]):
            return "Education & Courses"
        elif any(w in s for w in ["setup", "starter", "toolkit"]):
            return "Account & Setup"
        return "Core Fundamentals"

    elif category == "Tools & Integrations":
        if any(w in s for w in ["figma", "canva", "remotion", "video", "carousel"]):
            return "Creative & Design"
        elif any(w in s for w in ["lead", "scrape", "reddit", "apollo", "indeed"]):
            return "Data & Lead Generation"
        elif any(w in s for w in ["excel", "posthog", "graphify", "analytics"]):
            return "Analytics & Sheets"
        elif any(w in s for w in ["wispr", "cookiy", "bot"]):
            return "Voice & Browser Automations"
        return "Third-Party Connectors"

    elif category == "Prompts & Skills":
        if any(w in s for w in ["prompt", "prompts"]):
            return "Prompt Engineering"
        elif any(w in s for w in ["marketing", "ad", "copy"]):
            return "Marketing & Sales"
        elif any(w in s for w in ["safety", "security", "check", "audit"]):
            return "Security & Auditing"
        return "Custom Skills"

    elif category == "Building & Monetising":
        if any(w in s for w in ["client", "service", "sell", "agency", "inbound", "outreach"]):
            return "Agency & Client Acquisition"
        elif any(w in s for w in ["startup", "product", "saas", "cofounder"]):
            return "Startup & Products"
        elif any(w in s for w in ["automate", "process", "boring"]):
            return "Business Automation"
        return "Monetisation Strategy"

    return "General"


def normalize_raw_record(raw: Dict[str, Any]) -> ResourceRecord:
    """Normalize raw harvested record into a validated ResourceRecord model."""
    record_id = raw["id"]
    slug = raw["slug"]
    title = sanitize_csv_value(raw.get("title", "").strip())
    category = sanitize_csv_value(raw.get("category", "General").strip())
    difficulty = normalize_difficulty(raw.get("difficulty", "Beginner"))
    description = sanitize_csv_value(raw.get("description", "").strip())
    source_url = raw.get("source_url", "").strip()
    download_url = raw.get("download_url")
    author = raw.get("author", "Max Johnson")
    date = raw.get("date") or "2025"

    subcategory = derive_subcategory(category, slug, title)

    # Status conversion
    raw_status = raw.get("status", "WEB_ONLY")
    try:
        status = ContentStatus(raw_status)
    except ValueError:
        status = ContentStatus.WEB_ONLY

    topics = raw.get("topics", [])
    if category not in topics:
        topics.insert(0, category)
    if subcategory not in topics and subcategory != "General":
        topics.append(subcategory)

    ai_tools = raw.get("ai_tools", [])
    local_file = raw.get("local_file")
    local_html = raw.get("local_html")
    summary_file = f"summaries/{record_id}.md"
    notes = raw.get("notes", "")

    return ResourceRecord(
        id=record_id,
        slug=slug,
        title=title,
        category=category,
        subcategory=subcategory,
        difficulty=difficulty,
        description=description,
        source_url=source_url,
        download_url=download_url,
        content_type="Guide",
        author=author,
        date=date,
        topics=topics,
        ai_tools=ai_tools,
        status=status,
        local_file=local_file,
        local_html=local_html,
        summary_file=summary_file,
        copyright_status="Public Web / Personal Reference",
        notes=notes,
    )
