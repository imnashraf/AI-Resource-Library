"""Unit and integration tests for Phase 7: Offline Master Reference PDF Compilation."""

import re
from pathlib import Path
import pytest
from reportlab.platypus import Paragraph

from src.config import MASTER_PDF_PATH, SUMMARIES_DIR
from src.generators.pdf_engine import MasterPdfCompiler, parse_summary_sections, sanitize_text_for_xml
from src.generators.pdf_styles import (
    PAGE_WIDTH,
    PAGE_HEIGHT,
    PRINTABLE_WIDTH,
    TEAL_PRIMARY,
    get_pdf_styles,
)


def test_pdf_styles_definition():
    """Verify PDF styles, dimensions, and color tokens are correctly defined."""
    assert PAGE_WIDTH == 612.0
    assert PAGE_HEIGHT == 792.0
    assert PRINTABLE_WIDTH == 540.0
    assert TEAL_PRIMARY.hexval().lower() == "0x1a7a6a"

    styles = get_pdf_styles()
    required_style_names = [
        "CoverTitle",
        "CoverSubtitle",
        "PartTitle",
        "SectionHeading",
        "CardTitle",
        "CardSectionHeading",
        "Body",
        "BulletText",
        "TableHeader",
        "TableCell",
        "LegalNotice",
    ]
    for s_name in required_style_names:
        assert s_name in styles, f"Missing style {s_name}"


def test_sanitize_text_for_xml():
    """Verify text sanitization converts markdown to ReportLab tags without XML errors."""
    styles = get_pdf_styles()

    test_cases = [
        "Normal text without formatting",
        "Text with **bold** and *italic* formatting",
        "Code snippets like `claude --version` and `.env` files",
        "Unicode characters: arrows ->, dashes --, smart 'quotes' and \"double quotes\"",
        "Symbols with ampersands like & and angle brackets <tags>",
        "Non-breaking hyphens: Community\u2011hosted and ellipsis \u2026",
    ]

    for raw in test_cases:
        sanitized = sanitize_text_for_xml(raw)
        # Should build a ReportLab Paragraph without throwing
        p = Paragraph(sanitized, styles["Body"])
        assert p is not None


def test_parse_summary_sections():
    """Verify section parser reliably extracts sections 1 through 8 from summaries."""
    summary_file = SUMMARIES_DIR / "AI-001.md"
    assert summary_file.exists()

    content = summary_file.read_text(encoding="utf-8")
    sections = parse_summary_sections(content)

    for i in range(1, 9):
        key = f"section_{i}"
        assert key in sections, f"Missing {key} in parsed sections"
        assert len(sections[key]) > 20, f"Section {key} is unexpectedly short"


def test_pdf_compiler_custom_output(tmp_path):
    """Verify MasterPdfCompiler compiles successfully to a custom target path."""
    test_pdf = tmp_path / "TEST_MASTER.pdf"
    compiler = MasterPdfCompiler(output_path=test_pdf)
    result = compiler.compile_pdf()

    assert result.exists()
    assert result.stat().st_size > 100_000, f"Generated PDF unexpectedly small: {result.stat().st_size} bytes"

    raw_bytes = result.read_bytes()
    assert raw_bytes.startswith(b"%PDF-")


def test_master_pdf_deliverable_integrity():
    """Verify publication deliverable AI_RESOURCE_LIBRARY_MASTER.pdf meets all Gate 7 criteria."""
    assert MASTER_PDF_PATH.exists(), f"Deliverable PDF missing at {MASTER_PDF_PATH}"
    raw_bytes = MASTER_PDF_PATH.read_bytes()

    # 1. Valid PDF header
    assert raw_bytes.startswith(b"%PDF-"), "Invalid PDF header magic bytes"

    # 2. Page count >= 100
    page_matches = re.findall(rb"/Type\s*/Page\b", raw_bytes)
    page_count = len(page_matches)
    assert page_count >= 100, f"Expected >= 100 formatted pages, got {page_count}"

    # 3. PDF Bookmarks / Outline Hierarchy
    assert b"/Outlines" in raw_bytes, "Missing /Outlines entry in PDF catalog"

    # 4. All 71 resource IDs present
    for i in range(1, 72):
        res_id = f"AI-{i:03d}".encode("utf-8")
        assert res_id in raw_bytes, f"Resource {res_id.decode('utf-8')} missing from PDF binary"

    # 5. Statutory Fair Use and Attribution Notices present
    assert b"Fair Use" in raw_bytes
    assert b"AI Resource Library" in raw_bytes
