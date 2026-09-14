"""Configuration loader and system environment manager.

Loads settings.yaml and categories.yaml, and exposes standardized
pathlib.Path paths and runtime configurations.
"""

from pathlib import Path
from typing import Any, Dict, List
import yaml
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.yaml"
CATEGORIES_FILE = CONFIG_DIR / "categories.yaml"


def load_yaml(path: Path) -> Dict[str, Any]:
    """Safely load and parse a YAML file."""
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# Load raw dictionaries
SETTINGS = load_yaml(SETTINGS_FILE)
CATEGORIES_CONFIG = load_yaml(CATEGORIES_FILE)

# Derived directory paths
DELIVERABLES_ROOT = PROJECT_ROOT / SETTINGS.get("paths", {}).get("deliverables_root", "ai-resource-library")
INVENTORY_DIR = PROJECT_ROOT / SETTINGS.get("paths", {}).get("inventory_dir", "ai-resource-library/inventory")
DOCUMENTS_DIR = PROJECT_ROOT / SETTINGS.get("paths", {}).get("documents_dir", "ai-resource-library/documents")
WEB_PAGES_DIR = PROJECT_ROOT / SETTINGS.get("paths", {}).get("web_pages_dir", "ai-resource-library/web-pages")
SUMMARIES_DIR = PROJECT_ROOT / SETTINGS.get("paths", {}).get("summaries_dir", "ai-resource-library/summaries")
METADATA_DIR = PROJECT_ROOT / SETTINGS.get("paths", {}).get("metadata_dir", "ai-resource-library/metadata")
PDF_DIR = PROJECT_ROOT / SETTINGS.get("paths", {}).get("pdf_dir", "ai-resource-library/pdf")
LOGS_DIR = PROJECT_ROOT / SETTINGS.get("paths", {}).get("logs_dir", "ai-resource-library/logs")

MASTER_INDEX_PATH = PROJECT_ROOT / SETTINGS.get("paths", {}).get("master_index", "ai-resource-library/MASTER_INDEX.md")
LEARNING_ROADMAP_PATH = PROJECT_ROOT / SETTINGS.get("paths", {}).get("learning_roadmap", "ai-resource-library/LEARNING_ROADMAP.md")
PORTAL_HTML_PATH = PROJECT_ROOT / SETTINGS.get("paths", {}).get("portal_html", "ai-resource-library/library.html")
MASTER_PDF_PATH = PROJECT_ROOT / SETTINGS.get("paths", {}).get("master_pdf", "ai-resource-library/pdf/AI_RESOURCE_LIBRARY_MASTER.pdf")
FINAL_REPORT_PATH = PROJECT_ROOT / SETTINGS.get("paths", {}).get("final_report", "ai-resource-library/FINAL_REPORT.md")
PIPELINE_LOG_PATH = PROJECT_ROOT / SETTINGS.get("paths", {}).get("pipeline_log", "ai-resource-library/logs/pipeline.log")

# Category taxonomy definitions
CANONICAL_CATEGORIES: List[Dict[str, str]] = CATEGORIES_CONFIG.get("categories", [])
ROADMAP_DEFINITIONS: Dict[str, Any] = CATEGORIES_CONFIG.get("roadmaps", {})


def ensure_directories() -> None:
    """Ensure all required project directories exist on the filesystem."""
    for directory in [
        INVENTORY_DIR,
        DOCUMENTS_DIR,
        WEB_PAGES_DIR,
        SUMMARIES_DIR,
        METADATA_DIR,
        PDF_DIR,
        LOGS_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)
