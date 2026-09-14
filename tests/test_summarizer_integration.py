"""Integration tests for Phase 4: Validating all 71 generated summaries."""

from pathlib import Path
import pytest
from src.config import SUMMARIES_DIR
from src.summarizer.prompt_templates import validate_summary_structure, get_missing_sections


def test_all_71_summaries_exist_and_valid():
    """Verify that all 71 summaries exist and satisfy the 8-point schema."""
    assert SUMMARIES_DIR.exists(), f"Summaries directory does not exist: {SUMMARIES_DIR}"

    summary_files = list(SUMMARIES_DIR.glob("AI-*.md"))
    assert len(summary_files) >= 71, f"Expected 71 summaries, found {len(summary_files)}"

    for i in range(1, 72):
        res_id = f"AI-{i:03d}"
        fpath = SUMMARIES_DIR / f"{res_id}.md"
        assert fpath.exists(), f"Summary file missing: {fpath}"

        content = fpath.read_text(encoding="utf-8")
        assert len(content) > 500, f"Summary file suspiciously short: {fpath}"

        is_valid = validate_summary_structure(content)
        if not is_valid:
            missing = get_missing_sections(content)
            pytest.fail(f"Summary {res_id} missing mandatory sections: {missing}")

        words = content.split()
        assert len(words) >= 200, f"Summary {res_id} has insufficient depth ({len(words)} words)"
