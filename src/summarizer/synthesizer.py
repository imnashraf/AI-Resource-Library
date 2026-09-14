"""Analytical summary synthesizer and file caching manager."""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from src.config import SUMMARIES_DIR, WEB_PAGES_DIR
from src.ingestion.parser import GuideParser
from src.summarizer.prompt_templates import (
    SYSTEM_PROMPT,
    build_user_prompt,
    validate_summary_structure,
    get_missing_sections,
)
from src.summarizer.llm_client import LLMClient

logger = logging.getLogger("summarizer.synthesizer")


class SummarySynthesizer:
    """Manages prompt generation, LLM execution, structure verification, and caching."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

    def get_summary_path(self, resource_id: str) -> Path:
        """Get the filesystem path for a resource summary."""
        return SUMMARIES_DIR / f"{resource_id}.md"

    def is_summary_cached_and_valid(self, resource_id: str) -> bool:
        """Check if summary already exists on disk and is structurally valid."""
        path = self.get_summary_path(resource_id)
        if not path.exists() or path.stat().st_size < 300:
            return False
        content = path.read_text(encoding="utf-8")
        return validate_summary_structure(content)

    def extract_text_from_cached_html(self, record: Dict[str, Any]) -> tuple:
        """Extract article headings and body text from local cached HTML."""
        local_html = record.get("local_html")
        if not local_html:
            return [], record.get("description", "")

        html_path = WEB_PAGES_DIR.parent / local_html
        if not html_path.exists():
            return [], record.get("description", "")

        raw_html = html_path.read_text(encoding="utf-8")
        parsed = GuideParser.parse_guide_html(raw_html, base_url=record["source_url"], fallback_meta=record)
        return parsed["headings"], parsed["clean_text"]

    def synthesize_summary(self, record: Dict[str, Any], force: bool = False) -> str:
        """Generate or retrieve a validated 8-point markdown summary for a resource."""
        resource_id = record["id"]
        summary_path = self.get_summary_path(resource_id)

        # 1. Check local cache
        if not force and self.is_summary_cached_and_valid(resource_id):
            logger.debug("Summary cache hit for %s", resource_id)
            return summary_path.read_text(encoding="utf-8")

        # 2. Extract article context
        headings, body_text = self.extract_text_from_cached_html(record)
        if not body_text:
            body_text = record.get("description", "")

        # 3. Build prompt
        user_prompt = build_user_prompt(record, headings, body_text)

        # 4. Generate via LLM
        logger.info("Generating analytical summary for %s (%s)...", resource_id, record["title"])
        output = self.llm.generate_summary(SYSTEM_PROMPT, user_prompt)

        # 5. Validate structure
        if not validate_summary_structure(output):
            missing = get_missing_sections(output)
            logger.warning("Summary for %s missing sections: %s. Retrying with repair prompt...", resource_id, missing)

            repair_prompt = (
                f"{user_prompt}\n\n"
                f"CORRECTION: Your previous output missed the following mandatory headers: {missing}.\n"
                f"You MUST include all 8 numbered headers exactly as specified."
            )
            output = self.llm.generate_summary(SYSTEM_PROMPT, repair_prompt)

        # 6. Save to disk
        summary_path.write_text(output, encoding="utf-8")
        logger.info("Saved validated summary for %s to %s", resource_id, summary_path)
        return output
