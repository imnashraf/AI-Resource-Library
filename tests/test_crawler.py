"""Unit tests for SiteCrawler discovery logic."""

import pytest
from src.ingestion.crawler import SiteCrawler

SAMPLE_HOMEPAGE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Catalog</title></head>
<body>
<script>
guides = [
  { id: "test-guide-1", title: "Getting Started with AI", category: "Getting Started", difficulty: "Beginner", description: "Learn foundational concepts." },
  { id: "test-guide-2", title: "Advanced Claude Code", category: "Claude Code", difficulty: "Advanced", description: "Master CLI workflows." },
  { id: "test-guide-1", title: "Duplicate Guide", category: "Getting Started", difficulty: "Beginner", description: "Duplicate entry." }
];
</script>
</body>
</html>
"""


def test_extract_guides_from_html():
    """Verify regex discovery extracts unique guides with sequential IDs."""
    crawler = SiteCrawler()
    guides = crawler.extract_guides_from_html(SAMPLE_HOMEPAGE_HTML)

    assert len(guides) == 2, "Duplicate guide should be filtered out"
    first = guides[0]
    second = guides[1]

    assert first["id"] == "AI-001"
    assert first["slug"] == "test-guide-1"
    assert first["title"] == "Getting Started with AI"
    assert first["category"] == "Getting Started"
    assert first["difficulty"] == "Beginner"
    assert first["source_url"] == "https://aiwithmax.com/guide-test-guide-1.html"

    assert second["id"] == "AI-002"
    assert second["slug"] == "test-guide-2"
    assert second["difficulty"] == "Advanced"


def test_extract_guides_empty_html():
    """Verify empty or non-matching HTML returns an empty list without raising exceptions."""
    crawler = SiteCrawler()
    guides = crawler.extract_guides_from_html("<html><body>No guides here</body></html>")
    assert guides == []
