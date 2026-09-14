"""Unit tests for InventoryManager and CSV/JSON output integrity."""

import csv
import json
from pathlib import Path
import pytest
from src.config import INVENTORY_DIR, METADATA_DIR
from src.catalog.inventory import InventoryManager, CSV_FIELDNAMES


@pytest.fixture
def manager():
    return InventoryManager()


def test_build_and_export_inventory(manager):
    """Verify inventory generation produces valid CSV, JSON, and metadata files."""
    records = manager.generate_all()

    assert len(records) >= 65, f"Expected >= 65 records, got {len(records)}"

    # 1. Verify CSV exists and has exact headers
    csv_file = manager.csv_path
    assert csv_file.exists(), "master_inventory.csv does not exist"
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == CSV_FIELDNAMES, f"Fieldnames mismatch: {reader.fieldnames}"
        rows = list(reader)
        assert len(rows) == len(records)

    # 2. Verify JSON exists and matches records
    json_file = manager.json_path
    assert json_file.exists(), "master_inventory.json does not exist"
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == len(records)

    # 3. Verify per-resource metadata files exist
    meta_files = list(METADATA_DIR.glob("AI-*.json"))
    assert len(meta_files) == len(records)


def test_no_duplicate_ids_or_urls(manager):
    """Verify zero duplicate IDs and zero duplicate URLs in generated dataset."""
    records = manager.build_records(manager.load_raw_records())

    ids = [r.id for r in records]
    slugs = [r.slug for r in records]
    urls = [r.source_url for r in records if r.source_url]

    assert len(ids) == len(set(ids)), "Found duplicate IDs in inventory!"
    assert len(slugs) == len(set(slugs)), "Found duplicate slugs in inventory!"
    assert len(urls) == len(set(urls)), "Found duplicate URLs in inventory!"
