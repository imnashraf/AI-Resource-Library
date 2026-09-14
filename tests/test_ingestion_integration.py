"""Integration test verifying Phase 2 outputs."""

import json
from pathlib import Path
import pytest
from src.config import INVENTORY_DIR, WEB_PAGES_DIR


def test_harvested_records_completeness():
    """Verify raw_harvested_records.json contains >= 65 unique valid entries."""
    snapshot_path = INVENTORY_DIR / "raw_harvested_records.json"
    assert snapshot_path.exists(), "Snapshot file raw_harvested_records.json does not exist"

    with open(snapshot_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    assert len(records) >= 65, f"Expected >= 65 guides, found {len(records)}"

    seen_ids = set()
    seen_slugs = set()
    seen_urls = set()

    for r in records:
        # ID check
        assert r["id"].startswith("AI-")
        assert r["id"] not in seen_ids, f"Duplicate ID: {r['id']}"
        seen_ids.add(r["id"])

        # Slug check
        assert r["slug"] not in seen_slugs, f"Duplicate slug: {r['slug']}"
        seen_slugs.add(r["slug"])

        # URL check
        if r.get("source_url"):
            assert r["source_url"] not in seen_urls, f"Duplicate URL: {r['source_url']}"
            seen_urls.add(r["source_url"])

        # Required fields
        assert r["title"], f"Missing title for {r['id']}"
        assert r["category"], f"Missing category for {r['id']}"
        assert r["difficulty"], f"Missing difficulty for {r['id']}"
        assert r["status"] in ["DOWNLOADABLE", "WEB_ONLY", "RESTRICTED", "ERROR", "NOT_AVAILABLE"]

        # Local HTML existence
        html_rel_path = r["local_html"]
        assert html_rel_path is not None, f"Missing local_html path for {r['id']}"
        html_full_path = INVENTORY_DIR.parent / html_rel_path
        assert html_full_path.exists(), f"Cached HTML file does not exist: {html_full_path}"
        assert html_full_path.stat().st_size > 1000, f"HTML file suspiciously small: {html_full_path}"


def test_web_pages_directory_count():
    """Verify web-pages directory contains all harvested HTML files."""
    html_files = list(WEB_PAGES_DIR.glob("AI-*.html"))
    assert len(html_files) >= 65, f"Expected >= 65 HTML files in web-pages, found {len(html_files)}"
