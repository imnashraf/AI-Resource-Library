"""Unit and integration tests for Phase 8 Quality Control Audit Suite, Reporter, and CLI Orchestrator."""

import json
import subprocess
import sys
from pathlib import Path
import pytest

from src.config import (
    FINAL_REPORT_PATH,
    INVENTORY_DIR,
    MASTER_INDEX_PATH,
    MASTER_PDF_PATH,
    PORTAL_HTML_PATH,
    PROJECT_ROOT,
    SUMMARIES_DIR,
)
from src.audit.qc_checker import QualityControlChecker
from src.audit.reporter import FinalReportCompiler


def test_qc_checker_load_inventory():
    """Verify QualityControlChecker successfully loads master inventory records."""
    checker = QualityControlChecker()
    records = checker.load_inventory()
    assert isinstance(records, list)
    assert len(records) >= 65, f"Expected >= 65 records, got {len(records)}"


def test_qc_checker_deduplication():
    """Verify deduplication check finds zero duplicates in IDs, slugs, and source URLs."""
    checker = QualityControlChecker()
    records = checker.load_inventory()
    result = checker.check_deduplication(records)

    assert result["passed"] is True
    assert result["duplicate_ids"] == []
    assert result["duplicate_slugs"] == []
    assert result["duplicate_urls"] == []
    assert result["total_records"] == len(records)


def test_qc_checker_metadata_completeness():
    """Verify all records meet schema completeness standards."""
    checker = QualityControlChecker()
    records = checker.load_inventory()
    result = checker.check_metadata_completeness(records)

    assert result["passed"] is True
    assert result["missing_fields"] == {}
    assert result["invalid_difficulties"] == {}


def test_qc_checker_file_assets():
    """Verify all HTML web-pages, summaries, and metadata JSON files exist on disk with positive bytes."""
    checker = QualityControlChecker()
    records = checker.load_inventory()
    result = checker.check_file_assets(records)

    assert result["passed"] is True
    assert result["verified_asset_count"] == len(records) * 3
    assert result["missing_assets"] == []
    assert result["zero_byte_assets"] == []


def test_qc_checker_copyright_and_summaries():
    """Verify all summaries adhere to 8-point schema and Fair Use copyright guard."""
    checker = QualityControlChecker()
    records = checker.load_inventory()
    result = checker.check_copyright_and_summaries(records)

    assert result["passed"] is True
    assert result["invalid_schema"] == {}
    assert result["short_summaries"] == {}
    assert result["raw_html_leaks"] == []


def test_qc_checker_markdown_relative_links():
    """Verify cross-reference relative links in MASTER_INDEX.md and LEARNING_ROADMAP.md."""
    checker = QualityControlChecker()
    result = checker.check_markdown_relative_links()

    assert result["passed"] is True
    assert result["broken_links"] == []
    assert result["total_links_checked"] > 100


def test_qc_checker_web_portal():
    """Verify library.html is completely self-contained with zero external CDN references."""
    checker = QualityControlChecker()
    result = checker.check_web_portal()

    assert result["passed"] is True
    assert result["external_scripts"] == []
    assert result["external_stylesheets"] == []
    assert result["inlined_resource_count"] >= 65


def test_qc_checker_master_pdf():
    """Verify AI_RESOURCE_LIBRARY_MASTER.pdf meets length (>=100 pages) and bookmark requirements."""
    checker = QualityControlChecker()
    result = checker.check_master_pdf()

    assert result["passed"] is True
    assert result["page_count"] >= 100, f"Expected >= 100 pages, got {result['page_count']}"
    assert result["has_outlines"] is True
    assert result["is_valid_pdf"] is True


def test_qc_checker_full_audit():
    """Verify run_full_audit() executes all checks cleanly and passes."""
    checker = QualityControlChecker()
    results = checker.run_full_audit(check_urls=False)

    assert results["overall_passed"] is True
    assert results["total_cataloged"] >= 65
    assert results["deduplication"]["passed"] is True
    assert results["metadata_completeness"]["passed"] is True
    assert results["file_assets"]["passed"] is True
    assert results["copyright_and_summaries"]["passed"] is True
    assert results["markdown_links"]["passed"] is True
    assert results["web_portal"]["passed"] is True
    assert results["master_pdf"]["passed"] is True


def test_final_report_compiler_generation(tmp_path):
    """Verify FinalReportCompiler synthesizes and writes a valid FINAL_REPORT.md."""
    output_report = tmp_path / "TEST_FINAL_REPORT.md"
    compiler = FinalReportCompiler(output_path=output_report)

    written_path = compiler.write_report(check_urls=False)
    assert written_path.exists()
    assert written_path.stat().st_size > 5000

    content = written_path.read_text(encoding="utf-8")
    assert "# AI Resource Library — Quality Assurance & Final Compilation Report" in content
    assert "## 1. Executive Summary" in content
    assert "PASSED (Zero Defects)" in content
    assert "## 2. Quality Control Gate Results" in content
    assert "## 3. Catalog Taxonomy & Distribution Analysis" in content
    assert "## 4. Key AI Tools & Topic Frequencies" in content
    assert "## 5. Curated Learning Paths Summary" in content
    assert "## 6. Primary Deliverables Verification Checklist" in content
    assert "## 7. Sign-off & Recommendation" in content


def test_main_cli_orchestrator_audit():
    """Verify master CLI orchestrator executes --audit successfully."""
    cmd = [sys.executable, "main.py", "--audit"]
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, f"main.py --audit failed with output:\n{result.stderr}\n{result.stdout}"
    assert "EXECUTING PHASE 8: QA Audit & Final Report" in result.stdout
    assert "FINAL_REPORT.md" in result.stdout
    assert FINAL_REPORT_PATH.exists()
