"""Orchestrator for Phase 5: Markdown Index & Roadmap Compilers."""

import logging
from src.generators.index_generator import MasterIndexGenerator
from src.generators.roadmap_generator import LearningRoadmapGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("generators.main")


def run_generators_pipeline():
    """Generate MASTER_INDEX.md and LEARNING_ROADMAP.md."""
    logger.info("=== Starting Phase 5: Index & Roadmap Generation ===")

    # 1. Master Index
    index_gen = MasterIndexGenerator()
    index_file = index_gen.write_file()
    logger.info("Successfully generated MASTER_INDEX.md at %s", index_file)

    # 2. Learning Roadmap
    roadmap_gen = LearningRoadmapGenerator()
    roadmap_file = roadmap_gen.write_file()
    logger.info("Successfully generated LEARNING_ROADMAP.md at %s", roadmap_file)

    print(f"\n[Phase 5] Successfully generated:")
    print(f"  - {index_file}")
    print(f"  - {roadmap_file}")


if __name__ == "__main__":
    run_generators_pipeline()
