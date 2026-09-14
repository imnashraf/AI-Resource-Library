"""Unit tests for summarizer prompts, validation, and schema compliance."""

import pytest
from src.summarizer.prompt_templates import (
    validate_summary_structure,
    get_missing_sections,
    build_user_prompt,
)

SAMPLE_VALID_SUMMARY = """
# AI-001 - The Ultimate Claude Starter Setup Guide

- **Category:** Getting Started | **Subcategory:** Account & Setup
- **Difficulty:** Beginner
- **Source URL:** https://aiwithmax.com/guide-the-ultimate-claude-starter-setup-guide.html
- **Local Asset:** N/A (Web Only)
- **Status:** WEB_ONLY

## 1. What This Resource Teaches
This resource provides a comprehensive foundation for setting up and mastering Claude for personal and agency workflows.

## 2. Why It Matters
Configuring project memory and custom instructions prevents generic outputs and unlocks agentic productivity.

## 3. Target Audience
Beginners to intermediate AI practitioners looking to build reliable, structured assistants.

## 4. Key Concepts & Principles
- **Project Memory**: Persistent context across sessions.
- **Custom Instructions**: Guardrails and persona steering.

## 5. Tools & Technologies Mentioned
- **Claude Desktop**: Native environment.
- **Figma**: UI design integration via MCP.

## 6. Practical Use Cases & Workflows
- **Client Onboarding System**: Streamlined SOP setup.
- **Automated Research Pipeline**: Deep dive synthesis.

## 7. Prerequisites
A free or paid Anthropic Claude account and basic terminal familiarity.

## 8. Recommended Next Resources
- AI-002: The Master Level Claude Guide
"""

SAMPLE_INVALID_SUMMARY = """
# AI-001 - The Ultimate Claude Starter Setup Guide

## 1. What This Resource Teaches
A basic guide.

## 2. Why It Matters
Important for AI.
"""


def test_validate_summary_structure_valid():
    """Verify that a summary with all 8 headers passes validation."""
    assert validate_summary_structure(SAMPLE_VALID_SUMMARY) is True
    assert get_missing_sections(SAMPLE_VALID_SUMMARY) == []


def test_validate_summary_structure_invalid():
    """Verify that a summary with missing headers fails validation."""
    assert validate_summary_structure(SAMPLE_INVALID_SUMMARY) is False
    missing = get_missing_sections(SAMPLE_INVALID_SUMMARY)
    assert len(missing) == 6
    assert "3. Target Audience" in missing
    assert "8. Recommended Next Resources" in missing


def test_build_user_prompt():
    """Verify prompt builder formats metadata and headings properly."""
    record = {
        "id": "AI-001",
        "title": "Test Title",
        "category": "Getting Started",
        "subcategory": "Account & Setup",
        "difficulty": "Beginner",
        "source_url": "https://aiwithmax.com/test",
        "status": "WEB_ONLY",
        "author": "Max Johnson",
        "ai_tools": ["Claude", "Cursor"],
    }
    prompt = build_user_prompt(record, ["Heading 1", "Heading 2"], "Sample article body.")
    assert "AI-001" in prompt
    assert "Test Title" in prompt
    assert "Heading 1" in prompt
    assert "Claude, Cursor" in prompt
