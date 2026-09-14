"""Batch runner for Phase 4: LLM Analytical Summarizer."""

import json
import logging
from typing import List, Dict, Any
from tqdm import tqdm

from src.config import INVENTORY_DIR, SUMMARIES_DIR, LOGS_DIR
from src.summarizer.synthesizer import SummarySynthesizer
from src.summarizer.prompt_templates import validate_summary_structure

LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "summarizer.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("summarizer.main")


def run_summarizer_pipeline(force: bool = False) -> Dict[str, Any]:
    """Execute batch analytical summarization for all cataloged resources."""
    logger.info("=== Starting Phase 4: Analytical Summarizer Pipeline ===")

    json_inventory_path = INVENTORY_DIR / "master_inventory.json"
    if not json_inventory_path.exists():
        raise FileNotFoundError(f"Inventory missing at {json_inventory_path}. Run Phase 3 first.")

    with open(json_inventory_path, "r", encoding="utf-8") as f:
        records: List[Dict[str, Any]] = json.load(f)

    synthesizer = SummarySynthesizer()
    cache_hits = 0
    generated_count = 0
    validation_failures = 0

    print(f"\n[Phase 4] Synthesizing original summaries for {len(records)} resources...")

    for record in tqdm(records, desc="Summarizing Resources", unit="guide"):
        res_id = record["id"]

        if not force and synthesizer.is_summary_cached_and_valid(res_id):
            cache_hits += 1
            continue

        try:
            summary = synthesizer.synthesize_summary(record, force=force)
            generated_count += 1
            if not validate_summary_structure(summary):
                validation_failures += 1
        except Exception as exc:
            logger.error("Failed to generate summary for %s: %s", res_id, exc)
            validation_failures += 1

    logger.info("=== Phase 4 Summarizer Pipeline Complete ===")
    logger.info("Total records in inventory: %d", len(records))
    logger.info("Cache hits: %d", cache_hits)
    logger.info("New summaries generated: %d", generated_count)
    logger.info("Validation failures: %d", validation_failures)

    return {
        "total_records": len(records),
        "cache_hits": cache_hits,
        "generated": generated_count,
        "validation_failures": validation_failures,
    }


if __name__ == "__main__":
    run_summarizer_pipeline()
