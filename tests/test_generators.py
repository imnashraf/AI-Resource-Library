"""Unit and integration tests for Phase 5 Master Index and Learning Roadmap Compilers."""

import json
import re
from pathlib import Path
import pytest

from src.config import INVENTORY_DIR, MASTER_INDEX_PATH, LEARNING_ROADMAP_PATH, SUMMARIES_DIR
from src.generators.index_generator import MasterIndexGenerator, ORDERED_CATEGORIES
from src.generators.roadmap_generator import LearningRoadmapGenerator, ROADMAP_TRACKS, TRACK_DURATIONS


def test_index_generator_file_creation(tmp_path):
    """Test that MasterIndexGenerator builds a complete MASTER_INDEX.md without errors."""
    output_file = tmp_path / "TEST_MASTER_INDEX.md"
    gen = MasterIndexGenerator(output_path=output_file)
    result_path = gen.write_file()

    assert result_path.exists()
    assert result_path.stat().st_size > 1000

    content = result_path.read_text(encoding="utf-8")
    assert "# AI Resource Library — Master Index" in content
    assert "## Table of Contents" in content
    assert "## Complete Alphabetical & Numeric Lookup Table" in content


def test_index_generator_contains_all_resources():
    """Verify that MASTER_INDEX.md contains all resources from master_inventory.json."""
    inventory_path = INVENTORY_DIR / "master_inventory.json"
    with open(inventory_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    total_records = len(records)
    assert total_records >= 65, f"Expected >= 65 records in inventory, got {total_records}"

    content = MASTER_INDEX_PATH.read_text(encoding="utf-8")
    for r in records:
        res_id = r["id"]
        assert res_id in content, f"Resource {res_id} missing from MASTER_INDEX.md"
        assert f"summaries/{res_id}.md" in content, f"Summary link for {res_id} missing from MASTER_INDEX.md"


def test_index_generator_relative_links():
    """Verify every relative markdown link in MASTER_INDEX.md resolves to an existing file."""
    base_dir = MASTER_INDEX_PATH.parent
    text = MASTER_INDEX_PATH.read_text(encoding="utf-8")
    links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)

    checked = 0
    broken = []
    for label, target in links:
        if target.startswith("http://") or target.startswith("https://") or target.startswith("#"):
            continue
        clean_target = target.split("#")[0]
        if not clean_target:
            continue
        target_path = (base_dir / clean_target).resolve()
        checked += 1
        if not target_path.exists():
            broken.append((label, target, str(target_path)))

    assert checked > 0, "No relative links found to test in MASTER_INDEX.md"
    assert len(broken) == 0, f"Broken relative links found in MASTER_INDEX.md: {broken}"


def test_roadmap_generator_file_creation(tmp_path):
    """Test that LearningRoadmapGenerator builds LEARNING_ROADMAP.md without errors."""
    output_file = tmp_path / "TEST_LEARNING_ROADMAP.md"
    gen = LearningRoadmapGenerator(output_path=output_file)
    result_path = gen.write_file()

    assert result_path.exists()
    assert result_path.stat().st_size > 1000

    content = result_path.read_text(encoding="utf-8")
    assert "# AI Resource Library — Systematic Learning Roadmaps" in content
    assert "## Table of Contents" in content
    assert "## Master Multi-Path Prerequisite Matrix" in content


def test_roadmap_tracks_and_milestones():
    """Verify that all 8 paths (A through H) exist with all 5 mandatory milestone stages."""
    content = LEARNING_ROADMAP_PATH.read_text(encoding="utf-8")

    # 1. Check all 8 paths
    expected_paths = ["PATH A", "PATH B", "PATH C", "PATH D", "PATH E", "PATH F", "PATH G", "PATH H"]
    assert len(ROADMAP_TRACKS) == 8
    for p in expected_paths:
        assert f"## {p}:" in content, f"Missing {p} in LEARNING_ROADMAP.md"

    # 2. Check 5 mandatory milestone stages in order
    mandatory_stages = ["START HERE", "NEXT", "INTERMEDIATE", "ADVANCED", "CAPSTONE PROJECT"]
    for track in ROADMAP_TRACKS:
        track_stages = [s["stage"] for s in track["stages"]]
        assert track_stages == mandatory_stages, f"Track {track['path_id']} stages mismatch: {track_stages}"

    # 3. Check durations and rationales
    for p in expected_paths:
        assert p in TRACK_DURATIONS, f"Track duration mapping missing for {p}"

    assert content.count("Progression Rationale") >= 40, "Missing progression rationale across milestones"
    assert content.count("Estimated Time:") >= 40, "Missing estimated stage time across milestones"


def test_roadmap_generator_relative_links():
    """Verify every relative markdown link in LEARNING_ROADMAP.md resolves to an existing file."""
    base_dir = LEARNING_ROADMAP_PATH.parent
    text = LEARNING_ROADMAP_PATH.read_text(encoding="utf-8")
    links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)

    checked = 0
    broken = []
    for label, target in links:
        if target.startswith("http://") or target.startswith("https://") or target.startswith("#"):
            continue
        clean_target = target.split("#")[0]
        if not clean_target:
            continue
        target_path = (base_dir / clean_target).resolve()
        checked += 1
        if not target_path.exists():
            broken.append((label, target, str(target_path)))

    assert checked > 0, "No relative links found to test in LEARNING_ROADMAP.md"
    assert len(broken) == 0, f"Broken relative links found in LEARNING_ROADMAP.md: {broken}"


def test_generator_missing_inventory_raises(tmp_path):
    """Verify MasterIndexGenerator raises FileNotFoundError when inventory does not exist."""
    fake_inventory = tmp_path / "non_existent_inventory.json"
    gen = MasterIndexGenerator(inventory_path=fake_inventory)
    with pytest.raises(FileNotFoundError):
        gen.load_inventory()
