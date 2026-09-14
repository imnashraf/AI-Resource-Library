"""Environment and Scaffolding Verification Test.

Validates that all required packages can be imported and that all
directory structures and configuration files exist as specified.
"""

from pathlib import Path
import pytest


def test_required_imports():
    """Verify all core dependencies import cleanly."""
    import httpx
    import bs4
    import pydantic
    import reportlab
    import yaml
    import tqdm
    import dotenv
    import jinja2
    import groq

    assert httpx.__version__ is not None
    assert bs4.__version__ is not None
    assert pydantic.__version__ is not None
    assert reportlab.__version__ is not None


def test_directory_structure():
    """Verify all project deliverable directories exist."""
    from src.config import (
        INVENTORY_DIR,
        DOCUMENTS_DIR,
        WEB_PAGES_DIR,
        SUMMARIES_DIR,
        METADATA_DIR,
        PDF_DIR,
        LOGS_DIR,
    )

    for directory in [
        INVENTORY_DIR,
        DOCUMENTS_DIR,
        WEB_PAGES_DIR,
        SUMMARIES_DIR,
        METADATA_DIR,
        PDF_DIR,
        LOGS_DIR,
    ]:
        assert directory.exists(), f"Directory missing: {directory}"
        assert directory.is_dir(), f"Not a directory: {directory}"


def test_config_files():
    """Verify configuration files load valid contents."""
    from src.config import SETTINGS, CANONICAL_CATEGORIES, ROADMAP_DEFINITIONS

    assert "app" in SETTINGS
    assert "crawler" in SETTINGS
    assert "paths" in SETTINGS
    assert len(CANONICAL_CATEGORIES) >= 11
    assert len(ROADMAP_DEFINITIONS) == 8
