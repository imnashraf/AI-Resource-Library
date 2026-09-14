"""Unit and integration tests for Phase 6: Searchable Offline Web Portal (library.html)."""

import json
import re
from pathlib import Path
import pytest
from bs4 import BeautifulSoup

from src.config import INVENTORY_DIR, PORTAL_HTML_PATH, SUMMARIES_DIR
from src.generators.portal_builder import PortalBuilder
from src.summarizer.prompt_templates import validate_summary_structure


@pytest.fixture
def portal_soup():
    """Load and parse the generated library.html."""
    assert PORTAL_HTML_PATH.exists(), f"Portal HTML does not exist at {PORTAL_HTML_PATH}"
    content = PORTAL_HTML_PATH.read_text(encoding="utf-8")
    return BeautifulSoup(content, "html.parser")


def test_portal_builder_execution(tmp_path):
    """Test PortalBuilder runs cleanly and outputs a valid HTML file."""
    output_file = tmp_path / "test_library.html"
    builder = PortalBuilder(output_path=output_file)
    result = builder.write_portal()

    assert result.exists()
    assert result.stat().st_size > 100_000, f"Generated HTML file suspiciously small: {result.stat().st_size} bytes"

    content = result.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert '<script id="library-data" type="application/json">' in content


def test_air_gap_compliance_zero_external_dependencies(portal_soup):
    """Verify library.html has zero external CDN calls, scripts, or stylesheets."""
    # 1. External scripts
    scripts = portal_soup.find_all("script")
    external_scripts = [s.get("src") for s in scripts if s.get("src")]
    assert len(external_scripts) == 0, f"Found external scripts: {external_scripts}"

    # 2. External stylesheets
    links = portal_soup.find_all("link")
    external_styles = [
        l.get("href")
        for l in links
        if l.get("rel") == ["stylesheet"] or (l.get("href") and l.get("href").startswith("http"))
    ]
    assert len(external_styles) == 0, f"Found external stylesheets: {external_styles}"

    # 3. CSS imports in style tags
    styles = portal_soup.find_all("style")
    for style in styles:
        style_text = style.string or ""
        assert "@import url(http" not in style_text, "Found external @import in style tag"


def test_inlined_dataset_completeness(portal_soup):
    """Verify inlined JSON dataset contains all 71 resources with complete metadata."""
    data_script = portal_soup.find("script", id="library-data")
    assert data_script is not None, "Missing inlined <script id='library-data'>"

    raw_json = data_script.string
    assert raw_json is not None
    data = json.loads(raw_json)

    assert len(data) >= 65, f"Expected >= 65 resources, got {len(data)}"
    assert len(data) == 71, f"Expected exactly 71 resources, got {len(data)}"

    # Check that required keys exist on every record
    required_keys = ["id", "title", "category", "difficulty", "description", "source_url", "summary_markdown"]
    for item in data:
        for k in required_keys:
            assert k in item, f"Missing key {k} in item {item.get('id')}"


def test_all_summaries_in_portal_satisfy_8_point_schema(portal_soup):
    """Verify 100% of summaries in the portal dataset satisfy the 8-point schema."""
    data_script = portal_soup.find("script", id="library-data")
    data = json.loads(data_script.string)

    for item in data:
        res_id = item["id"]
        sm = item.get("summary_markdown", "")
        assert len(sm) > 200, f"Summary for {res_id} is suspiciously short"
        assert validate_summary_structure(sm), f"Summary for {res_id} failed 8-point schema validation"


def test_dom_elements_structure(portal_soup):
    """Verify all required interactive DOM elements exist in the portal HTML."""
    # Brand & Header
    assert portal_soup.find("header") is not None
    assert "Nabil AI Resource Library" in portal_soup.get_text()

    # Circular Avatar Uploader
    assert portal_soup.find("div", id="avatar-uploader") is not None
    assert portal_soup.find("img", id="avatar-img") is not None
    assert portal_soup.find("input", id="avatar-file-input") is not None

    # Centered Filter Containers
    assert portal_soup.find("div", id="category-pills") is not None
    assert portal_soup.find("div", id="difficulty-pills") is not None

    # Verified Removed Elements (Search, Filter/Sort Selects, Copy Markdown)
    assert portal_soup.find("input", id="search-input") is None
    assert portal_soup.find("button", id="search-clear-btn") is None
    assert portal_soup.find("select", id="tool-filter-select") is None
    assert portal_soup.find("select", id="access-filter-select") is None
    assert portal_soup.find("select", id="sort-select") is None
    assert portal_soup.find("button", id="reset-filters-btn") is None
    assert portal_soup.find("button", id="modal-copy-btn") is None
    assert portal_soup.find("a", id="modal-local-html") is None
    assert portal_soup.find("a", id="modal-local-md") is None

    # Results & Grid
    assert portal_soup.find("div", id="results-count") is not None
    assert portal_soup.find("div", id="resource-grid") is not None

    # Summary Modal
    modal = portal_soup.find("div", id="summary-modal")
    assert modal is not None
    assert portal_soup.find("button", id="modal-close-btn") is not None
    assert portal_soup.find("div", id="modal-body") is not None


def test_local_asset_links_resolve_on_disk(portal_soup):
    """Verify local files referenced in the portal dataset exist on disk."""
    data_script = portal_soup.find("script", id="library-data")
    data = json.loads(data_script.string)

    base_dir = PORTAL_HTML_PATH.parent
    for item in data:
        res_id = item["id"]
        # local_html check
        local_html = item.get("local_html")
        if local_html:
            html_path = base_dir / local_html
            assert html_path.exists(), f"Referenced local HTML file missing for {res_id}: {html_path}"

        # summary_file check
        summary_file = item.get("summary_file")
        if summary_file:
            sum_path = base_dir / summary_file
            assert sum_path.exists(), f"Referenced summary file missing for {res_id}: {sum_path}"
