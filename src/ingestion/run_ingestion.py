"""Main execution script for Phase 2: Ingestion, Site Discovery & Asset Downloader."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm

from src.config import SETTINGS, LOGS_DIR, INVENTORY_DIR
from src.ingestion.rate_limiter import ResilientHttpClient
from src.ingestion.crawler import SiteCrawler
from src.ingestion.downloader import AssetDownloader

# Configure logging
LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / "ingestion.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("ingestion.main")


def run_ingestion_pipeline() -> List[Dict[str, Any]]:
    """Execute complete discovery, page archival, and asset downloading."""
    logger.info("=== Starting Phase 2: Ingestion & Asset Acquisition ===")

    with ResilientHttpClient() as client:
        # Step 1: Discover guides
        crawler = SiteCrawler(http_client=client)
        discovered_guides = crawler.discover_guides()
        logger.info("Discovered %d guides from catalog.", len(discovered_guides))

        if not discovered_guides:
            raise RuntimeError("Zero guides discovered from homepage! Check network or parser.")

        # Step 2: Process each guide
        downloader = AssetDownloader(http_client=client)
        processed_records = []

        print(f"\n[Phase 2] Harvesting {len(discovered_guides)} guides from aiwithmax.com...")
        for guide_meta in tqdm(discovered_guides, desc="Ingesting Guides", unit="guide"):
            processed = downloader.process_guide(guide_meta)
            processed_records.append(processed)

        # Save intermediate snapshot for Phase 3
        INVENTORY_DIR.mkdir(parents=True, exist_ok=True)
        raw_snapshot_path = INVENTORY_DIR / "raw_harvested_records.json"
        with open(raw_snapshot_path, "w", encoding="utf-8") as f:
            # Strip parsed_content DOM objects before saving JSON
            serializable_records = []
            for rec in processed_records:
                clean_rec = {k: v for k, v in rec.items() if k != "parsed_content"}
                serializable_records.append(clean_rec)
            json.dump(serializable_records, f, indent=2, ensure_ascii=False)

        # Calculate statistics
        status_counts = {}
        for r in processed_records:
            st = r.get("status", "UNKNOWN")
            status_counts[st] = status_counts.get(st, 0) + 1

        logger.info("=== Phase 2 Ingestion Complete ===")
        logger.info("Total guides processed: %d", len(processed_records))
        logger.info("Status distribution: %s", status_counts)
        logger.info("Raw snapshot saved to: %s", raw_snapshot_path)

        return processed_records


if __name__ == "__main__":
    run_ingestion_pipeline()
