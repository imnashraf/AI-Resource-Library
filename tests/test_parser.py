"""Unit tests for GuideParser DOM extraction logic."""

import pytest
from src.ingestion.parser import GuideParser

SAMPLE_GUIDE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>The Ultimate Claude Starter Setup Guide</title>
</head>
<body>
    <header class="header">
        <span class="author-name">Max Johnson</span>
    </header>
    <div class="guide-hero">
        <span class="badge badge-cat">Getting Started</span>
        <span class="badge badge-diff">Beginner</span>
        <h1>The Ultimate Claude Starter Setup Guide</h1>
    </div>
    <div class="page-wrap">
        <aside class="toc-sidebar">
            <div class="toc-box">
                <ol>
                    <li><a href="#ch1">Chapter 01: Basics</a></li>
                    <li><a href="#ch2">Chapter 02: Advanced</a></li>
                </ol>
            </div>
        </aside>
        <article class="guide-content">
            <h2>Chapter 01: Basics</h2>
            <p>Welcome to Claude Code setup. This guide uses Cursor and Groq.</p>
            <p>For more details, visit <a href="https://anthropic.com">Anthropic</a>.</p>
            <p>Download our cheat sheet: <a href="downloads/cheatsheet.pdf">Download PDF Cheatsheet</a></p>
            <h2>Chapter 02: Advanced</h2>
            <p>Integrate n8n and Supabase for complete automation.</p>
        </article>
    </div>
</body>
</html>
"""


def test_parse_guide_html():
    """Verify DOM parser extracts all structured fields accurately."""
    parsed = GuideParser.parse_guide_html(
        SAMPLE_GUIDE_HTML,
        base_url="https://aiwithmax.com/guide-the-ultimate-claude-starter-setup-guide.html",
    )

    assert parsed["title"] == "The Ultimate Claude Starter Setup Guide"
    assert parsed["author"] == "Max Johnson"
    assert parsed["category"] == "Getting Started"
    assert parsed["difficulty"] == "Beginner"
    assert len(parsed["toc"]) == 2
    assert "Chapter 01: Basics" in parsed["headings"]
    assert "Chapter 02: Advanced" in parsed["headings"]

    # Tool detection
    assert "Claude Code" in parsed["ai_tools"]
    assert "Cursor" in parsed["ai_tools"]
    assert "Groq" in parsed["ai_tools"]
    assert "n8n" in parsed["ai_tools"]
    assert "Supabase" in parsed["ai_tools"]

    # Links
    assert len(parsed["download_links"]) == 1
    assert parsed["download_links"][0]["url"] == "https://aiwithmax.com/downloads/cheatsheet.pdf"
    assert any("anthropic.com" in link["url"] for link in parsed["outbound_links"])
