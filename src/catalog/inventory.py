"""Master inventory generator and persistence manager.

Generates master CSV, master JSON, and granular per-resource metadata files
from raw harvested data.
"""

import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from src.config import INVENTORY_DIR, METADATA_DIR
from src.catalog.models import ResourceRecord
from src.catalog.normalizer import normalize_raw_record

logger = logging.getLogger("catalog.inventory")

CSV_FIELDNAMES = [
    "ID",
    "Title",
    "Category",
    "Subcategory",
    "Difficulty",
    "Description",
    "Source URL",
    "Download URL",
    "Content Type",
    "Author",
    "Date",
    "Topics",
    "AI Tools",
    "Status",
    "Local File",
    "Copyright/Reuse Status",
    "Notes",
]


class InventoryManager:
    """Manages creation and verification of master CSV and JSON inventories."""

    def __init__(self):
        INVENTORY_DIR.mkdir(parents=True, exist_ok=True)
        METADATA_DIR.mkdir(parents=True, exist_ok=True)
        self.csv_path = INVENTORY_DIR / "master_inventory.csv"
        self.json_path = INVENTORY_DIR / "master_inventory.json"
        self.raw_snapshot_path = INVENTORY_DIR / "raw_harvested_records.json"

    def load_raw_records(self) -> List[Dict[str, Any]]:
        """Load raw harvested records from snapshot."""
        if not self.raw_snapshot_path.exists():
            raise FileNotFoundError(
                f"Raw harvested records not found at {self.raw_snapshot_path}. Run Phase 2 first."
            )
        with open(self.raw_snapshot_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def build_records(self, raw_records: List[Dict[str, Any]]) -> List[ResourceRecord]:
        """Normalize and validate all records into ResourceRecord instances."""
        records = []
        for raw in raw_records:
            rec = normalize_raw_record(raw)
            records.append(rec)
        logger.info("Successfully built and validated %d ResourceRecord instances.", len(records))
        return records

    def export_csv(self, records: List[ResourceRecord]) -> Path:
        """Export master inventory to CSV with full quoting to prevent delimiter/formula issues."""
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for r in records:
                writer.writerow(r.to_csv_dict())

        logger.info("Master CSV inventory written to %s (%d rows)", self.csv_path, len(records))
        return self.csv_path

    def export_json(self, records: List[ResourceRecord]) -> Path:
        """Export master inventory to a consolidated JSON file."""
        data = [r.model_dump() for r in records]
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info("Master JSON inventory written to %s (%d items)", self.json_path, len(records))
        return self.json_path

    def export_metadata_files(self, records: List[ResourceRecord]) -> int:
        """Export individual granular metadata JSON files for each resource."""
        count = 0
        for r in records:
            file_path = METADATA_DIR / f"{r.id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(r.model_dump(), f, indent=2, ensure_ascii=False)
            count += 1

        logger.info("Exported %d per-resource metadata files into %s", count, METADATA_DIR)
        return count

    def generate_all(self) -> List[ResourceRecord]:
        """Orchestrate end-to-end normalization and export."""
        raw_records = self.load_raw_records()
        records = self.build_records(raw_records)
        self.export_csv(records)
        self.export_json(records)
        self.export_metadata_files(records)
        return records


if __name__ == "__main__":
    manager = InventoryManager()
    records = manager.generate_all()
    print(f"Successfully generated inventories for {len(records)} resources.")
