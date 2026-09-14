"""Website discovery crawler for aiwithmax.com.

Extracts all guide listings from the target website catalog, normalizes
entries, and assigns sequential unique IDs.
"""

import re
import html
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from src.config import SETTINGS
from src.ingestion.rate_limiter import ResilientHttpClient

logger = logging.getLogger("ingestion.crawler")


class SiteCrawler:
    """Discovers and catalogs guides from the live aiwithmax.com website."""

    def __init__(self, http_client: Optional[ResilientHttpClient] = None):
        crawler_cfg = SETTINGS.get("crawler", {})
        self.base_url = crawler_cfg.get("base_url", "https://aiwithmax.com/")
        self.id_prefix = SETTINGS.get("app", {}).get("id_prefix", "AI")
        self.client = http_client or ResilientHttpClient()
        self._owns_client = http_client is None

    def fetch_homepage(self) -> str:
        """Download the target homepage HTML."""
        logger.info("Fetching homepage: %s", self.base_url)
        response = self.client.get(self.base_url)
        response.raise_for_status()
        return response.text

    def extract_guides_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract the catalog of guides from the embedded JavaScript array."""
        pattern = (
            r'\{\s*id:\s*[\"\']([^\"\']+)[\"\'],\s*'
            r'title:\s*[\"\'](.*?)[\"\'],\s*'
            r'category:\s*[\"\'](.*?)[\"\'],\s*'
            r'difficulty:\s*[\"\'](.*?)[\"\'],\s*'
            r'description:\s*[\"\'](.*?)[\"\']\s*\}'
        )
        matches = re.findall(pattern, html_content, re.DOTALL)
        if not matches:
            logger.warning("Regex extraction returned zero matches from HTML payload.")
            return []

        guides = []
        seen_slugs = set()
        idx = 1

        for slug, title, category, difficulty, description in matches:
            slug = slug.strip()
            if slug in seen_slugs:
                logger.warning("Skipping duplicate slug: %s", slug)
                continue
            seen_slugs.add(slug)

            # Unescape and sanitize strings
            clean_title = html.unescape(title).strip()
            clean_category = html.unescape(category).strip()
            clean_difficulty = html.unescape(difficulty).strip()
            clean_desc = html.unescape(description).strip()

            resource_id = f"{self.id_prefix}-{idx:03d}"
            guide_url = urljoin(self.base_url, f"guide-{slug}.html")

            guides.append(
                {
                    "id": resource_id,
                    "index": idx,
                    "slug": slug,
                    "title": clean_title,
                    "category": clean_category,
                    "difficulty": clean_difficulty,
                    "description": clean_desc,
                    "source_url": guide_url,
                }
            )
            idx += 1

        logger.info("Successfully discovered %d unique guides.", len(guides))
        return guides

    def discover_guides(self) -> List[Dict[str, Any]]:
        """High-level discovery method: fetches homepage and returns guide metadata."""
        homepage_html = self.fetch_homepage()
        return self.extract_guides_from_html(homepage_html)

    def close(self) -> None:
        """Close HTTP client if owned."""
        if self._owns_client and self.client:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
