"""Asset downloader and web-page archiver.

Handles downloading of permitted public documents, caching of raw HTML,
and classification of resources into DOWNLOADABLE, WEB_ONLY, or RESTRICTED.
"""

import re
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from src.config import SETTINGS, WEB_PAGES_DIR, DOCUMENTS_DIR
from src.ingestion.rate_limiter import ResilientHttpClient
from src.ingestion.parser import GuideParser

logger = logging.getLogger("ingestion.downloader")


def sanitize_filename(name: str) -> str:
    """Sanitize title for safe cross-platform filesystem filenames."""
    sanitized = re.sub(r'[\\/*?:"<>|]', '', name)
    sanitized = re.sub(r'\s+', '_', sanitized.strip())
    return sanitized[:75]


class AssetDownloader:
    """Downloads assets and archives web pages for individual guides."""

    def __init__(self, http_client: Optional[ResilientHttpClient] = None):
        self.client = http_client or ResilientHttpClient()
        self._owns_client = http_client is None
        self.max_size_mb = SETTINGS.get("downloader", {}).get("max_file_size_mb", 50)
        self.allowed_exts = set(
            SETTINGS.get("downloader", {}).get(
                "allowed_extensions", [".pdf", ".docx", ".xlsx", ".csv", ".txt", ".md", ".zip"]
            )
        )
        WEB_PAGES_DIR.mkdir(parents=True, exist_ok=True)
        DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    def process_guide(self, guide_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch, parse, archive HTML, and handle any downloadable assets for a guide."""
        guide_id = guide_meta["id"]
        slug = guide_meta["slug"]
        source_url = guide_meta["source_url"]

        html_filename = f"{guide_id}_{slug}.html"
        html_path = WEB_PAGES_DIR / html_filename

        # 1. Fetch or load cached HTML
        if html_path.exists() and html_path.stat().st_size > 500:
            logger.debug("Loading cached HTML for %s (%s)", guide_id, slug)
            raw_html = html_path.read_text(encoding="utf-8")
        else:
            logger.info("Fetching guide page for %s: %s", guide_id, source_url)
            try:
                response = self.client.get(source_url)
                if response.status_code == 404:
                    logger.warning("Guide %s returned 404: %s", guide_id, source_url)
                    return {
                        **guide_meta,
                        "status": "NOT_AVAILABLE",
                        "local_html": None,
                        "local_file": None,
                        "download_url": None,
                        "parsed_content": None,
                        "notes": "Guide page returned 404 on target server",
                    }
                response.raise_for_status()
                raw_html = response.text
                html_path.write_text(raw_html, encoding="utf-8")
            except Exception as exc:
                logger.error("Error fetching %s (%s): %s", guide_id, source_url, exc)
                return {
                    **guide_meta,
                    "status": "ERROR",
                    "local_html": None,
                    "local_file": None,
                    "download_url": None,
                    "parsed_content": None,
                    "notes": f"Fetch error: {exc}",
                }

        # 2. Parse HTML
        parsed = GuideParser.parse_guide_html(raw_html, base_url=source_url, fallback_meta=guide_meta)

        # 3. Check for downloadable assets
        download_links = parsed.get("download_links", [])
        status = "WEB_ONLY"
        local_file = None
        download_url = None
        notes = "Public web guide cataloged"

        if download_links:
            target_link = download_links[0]["url"]
            download_url = target_link
            ext = Path(urlparse(target_link).path).suffix.lower()

            if ext not in self.allowed_exts and not target_link.lower().endswith(".pdf"):
                logger.info("External link requires platform/auth: %s", target_link)
                status = "RESTRICTED"
                notes = "Asset hosted on external platform; full download not permitted"
            else:
                # Attempt polite download
                clean_title = sanitize_filename(parsed["title"])
                target_ext = ext if ext in self.allowed_exts else ".pdf"
                dest_filename = f"{guide_id}_{clean_title}{target_ext}"
                dest_path = DOCUMENTS_DIR / dest_filename

                if dest_path.exists() and dest_path.stat().st_size > 0:
                    status = "DOWNLOADABLE"
                    local_file = str(dest_path.relative_to(dest_path.parent.parent))
                    notes = "Downloaded official document (cached)"
                else:
                    try:
                        logger.info("Downloading asset for %s: %s", guide_id, target_link)
                        doc_resp = self.client.get(target_link)
                        doc_resp.raise_for_status()

                        # Verify Content-Length
                        content_len = len(doc_resp.content)
                        if content_len > self.max_size_mb * 1024 * 1024:
                            status = "WEB_ONLY"
                            notes = f"Asset exceeds {self.max_size_mb}MB limit"
                        else:
                            dest_path.write_bytes(doc_resp.content)
                            status = "DOWNLOADABLE"
                            local_file = str(dest_path.relative_to(dest_path.parent.parent))
                            notes = "Successfully downloaded official document"
                    except Exception as exc:
                        logger.warning("Failed to download %s: %s", target_link, exc)
                        status = "ERROR"
                        notes = f"Download failed: {exc}"

        return {
            **guide_meta,
            "title": parsed["title"],
            "author": parsed["author"],
            "category": parsed["category"],
            "difficulty": parsed["difficulty"],
            "status": status,
            "download_url": download_url,
            "local_file": local_file,
            "local_html": str(html_path.relative_to(html_path.parent.parent)),
            "topics": parsed["topics"],
            "ai_tools": parsed["ai_tools"],
            "notes": notes,
            "parsed_content": parsed,
        }

    def close(self) -> None:
        """Close HTTP client if owned."""
        if self._owns_client and self.client:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
