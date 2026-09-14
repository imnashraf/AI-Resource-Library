"""Quality Control & Data Integrity Audit Suite.

Runs comprehensive validation across all generated artifacts:
- Deduplication of IDs, slugs, and source URLs
- Metadata completeness and schema adherence
- File asset presence and byte size on disk
- Copyright and 8-point summary structural compliance
- Markdown relative link cross-reference integrity
- Zero-CDN offline air-gap compliance of library.html
- Master PDF completeness, bookmarks, and page budget (>= 100 pages)
- Source URL integrity and HTTP health checks
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import httpx
from bs4 import BeautifulSoup

from src.config import (
    DOCUMENTS_DIR,
    INVENTORY_DIR,
    LEARNING_ROADMAP_PATH,
    MASTER_INDEX_PATH,
    MASTER_PDF_PATH,
    METADATA_DIR,
    PORTAL_HTML_PATH,
    SUMMARIES_DIR,
    WEB_PAGES_DIR,
)
from src.summarizer.prompt_templates import validate_summary_structure, get_missing_sections

logger = logging.getLogger("audit.qc")


class QualityControlChecker:
    """Executes all quality assurance gates and produces structured audit telemetry."""

    def __init__(
        self,
        inventory_path: Optional[Path] = None,
        deliverables_dir: Optional[Path] = None,
    ):
        self.inventory_path = inventory_path or (INVENTORY_DIR / "master_inventory.json")
        self.deliverables_dir = deliverables_dir or (INVENTORY_DIR.parent)

    def load_inventory(self) -> List[Dict[str, Any]]:
        """Load and return records from master_inventory.json."""
        if not self.inventory_path.exists():
            raise FileNotFoundError(f"Master inventory missing at {self.inventory_path}")
        with open(self.inventory_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def check_deduplication(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify zero duplicate IDs, slugs, or source URLs."""
        ids = [r["id"] for r in records]
        slugs = [r["slug"] for r in records]
        urls = [r["source_url"] for r in records if r.get("source_url")]

        dup_ids = [x for x in ids if ids.count(x) > 1]
        dup_slugs = [x for x in slugs if slugs.count(x) > 1]
        dup_urls = [x for x in urls if urls.count(x) > 1]

        passed = (len(dup_ids) == 0 and len(dup_slugs) == 0 and len(dup_urls) == 0)
        return {
            "passed": passed,
            "total_records": len(records),
            "duplicate_ids": list(set(dup_ids)),
            "duplicate_slugs": list(set(dup_slugs)),
            "duplicate_urls": list(set(dup_urls)),
        }

    def check_metadata_completeness(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify all mandatory fields are present and valid."""
        required_fields = [
            "id", "slug", "title", "category", "subcategory",
            "difficulty", "description", "content_type",
            "topics", "ai_tools", "status", "summary_file"
        ]
        valid_difficulties = {"Beginner", "Intermediate", "Advanced", "Beginner to Advanced"}

        missing_fields = {}
        invalid_difficulties = {}

        for r in records:
            res_id = r.get("id", "UNKNOWN")
            for field in required_fields:
                if field not in r or r[field] is None or r[field] == "":
                    missing_fields.setdefault(res_id, []).append(field)

            diff = r.get("difficulty")
            if diff not in valid_difficulties:
                invalid_difficulties[res_id] = diff

        passed = (len(missing_fields) == 0 and len(invalid_difficulties) == 0)
        return {
            "passed": passed,
            "missing_fields": missing_fields,
            "invalid_difficulties": invalid_difficulties,
        }

    def check_file_assets(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify referenced files exist on disk with positive byte sizes."""
        missing_assets = []
        zero_byte_assets = []
        verified_count = 0

        for r in records:
            res_id = r["id"]

            # 1. local_html check
            local_html = r.get("local_html")
            if local_html:
                p = self.deliverables_dir / local_html
                if not p.exists():
                    missing_assets.append((res_id, "local_html", str(p)))
                elif p.stat().st_size == 0:
                    zero_byte_assets.append((res_id, "local_html", str(p)))
                else:
                    verified_count += 1

            # 2. summary_file check
            summary_file = r.get("summary_file")
            if summary_file:
                p = self.deliverables_dir / summary_file
                if not p.exists():
                    missing_assets.append((res_id, "summary_file", str(p)))
                elif p.stat().st_size == 0:
                    zero_byte_assets.append((res_id, "summary_file", str(p)))
                else:
                    verified_count += 1

            # 3. metadata JSON file
            meta_path = METADATA_DIR / f"{res_id}.json"
            if not meta_path.exists():
                missing_assets.append((res_id, "metadata_json", str(meta_path)))
            elif meta_path.stat().st_size == 0:
                zero_byte_assets.append((res_id, "metadata_json", str(meta_path)))
            else:
                verified_count += 1

        passed = (len(missing_assets) == 0 and len(zero_byte_assets) == 0)
        return {
            "passed": passed,
            "verified_asset_count": verified_count,
            "missing_assets": missing_assets,
            "zero_byte_assets": zero_byte_assets,
        }

    def check_copyright_and_summaries(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify 100% of summaries satisfy 8-point schema with zero verbatim HTML."""
        invalid_schema = {}
        short_summaries = {}
        raw_html_leaks = []

        html_tag_pattern = re.compile(r"<(script|style|div|span|article|header|nav|footer)[^>]*>", re.IGNORECASE)

        for r in records:
            res_id = r["id"]
            sum_path = SUMMARIES_DIR / f"{res_id}.md"

            if not sum_path.exists():
                invalid_schema[res_id] = ["FILE_NOT_FOUND"]
                continue

            text = sum_path.read_text(encoding="utf-8")
            words = text.split()

            if len(words) < 200:
                short_summaries[res_id] = len(words)

            if not validate_summary_structure(text):
                invalid_schema[res_id] = get_missing_sections(text)

            # Check for raw scraped HTML markup leakage
            if html_tag_pattern.search(text):
                raw_html_leaks.append(res_id)

        passed = (len(invalid_schema) == 0 and len(short_summaries) == 0 and len(raw_html_leaks) == 0)
        return {
            "passed": passed,
            "total_summaries": len(records),
            "invalid_schema": invalid_schema,
            "short_summaries": short_summaries,
            "raw_html_leaks": raw_html_leaks,
        }

    def check_markdown_relative_links(self) -> Dict[str, Any]:
        """Verify all relative links in MASTER_INDEX.md and LEARNING_ROADMAP.md resolve on disk."""
        files_to_check = [MASTER_INDEX_PATH, LEARNING_ROADMAP_PATH]
        broken_links = []
        total_checked = 0

        for doc_path in files_to_check:
            if not doc_path.exists():
                broken_links.append((str(doc_path), "DOCUMENT_NOT_FOUND", ""))
                continue

            base_dir = doc_path.parent
            text = doc_path.read_text(encoding="utf-8")
            links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)

            for label, target in links:
                if target.startswith("http://") or target.startswith("https://") or target.startswith("#"):
                    continue
                clean_target = target.split("#")[0]
                if not clean_target:
                    continue
                resolved = (base_dir / clean_target).resolve()
                total_checked += 1
                if not resolved.exists():
                    broken_links.append((doc_path.name, label, target))

        passed = (len(broken_links) == 0)
        return {
            "passed": passed,
            "total_links_checked": total_checked,
            "broken_links": broken_links,
        }

    def check_web_portal(self) -> Dict[str, Any]:
        """Verify library.html exists, is air-gapped (0 CDNs), and contains complete dataset."""
        if not PORTAL_HTML_PATH.exists():
            return {"passed": False, "error": f"library.html not found at {PORTAL_HTML_PATH}"}

        content = PORTAL_HTML_PATH.read_text(encoding="utf-8")
        soup = BeautifulSoup(content, "html.parser")

        # Check external dependencies
        scripts = soup.find_all("script")
        external_scripts = [s.get("src") for s in scripts if s.get("src")]
        links = soup.find_all("link")
        external_styles = [
            l.get("href") for l in links
            if l.get("rel") == ["stylesheet"] or (l.get("href") and l.get("href").startswith("http"))
        ]

        # Check inlined data
        data_script = soup.find("script", id="library-data")
        inlined_count = 0
        if data_script and data_script.string:
            try:
                data = json.loads(data_script.string)
                inlined_count = len(data)
            except Exception:
                inlined_count = -1

        passed = (
            len(external_scripts) == 0
            and len(external_styles) == 0
            and inlined_count >= 65
            and PORTAL_HTML_PATH.stat().st_size > 50_000
        )
        return {
            "passed": passed,
            "file_size": PORTAL_HTML_PATH.stat().st_size,
            "external_scripts": external_scripts,
            "external_stylesheets": external_styles,
            "inlined_resource_count": inlined_count,
        }

    def check_master_pdf(self) -> Dict[str, Any]:
        """Verify AI_RESOURCE_LIBRARY_MASTER.pdf meets page budget and contains bookmarks."""
        if not MASTER_PDF_PATH.exists():
            return {"passed": False, "error": f"Master PDF not found at {MASTER_PDF_PATH}"}

        raw = MASTER_PDF_PATH.read_bytes()
        is_valid_pdf = raw.startswith(b"%PDF-")
        page_matches = re.findall(rb"/Type\s*/Page\b", raw)
        page_count = len(page_matches)
        has_outlines = b"/Outlines" in raw

        passed = is_valid_pdf and page_count >= 100 and has_outlines
        return {
            "passed": passed,
            "file_size": len(raw),
            "is_valid_pdf": is_valid_pdf,
            "page_count": page_count,
            "has_outlines": has_outlines,
        }

    def check_url_health(self, records: List[Dict[str, Any]], sample_size: Optional[int] = None) -> Dict[str, Any]:
        """Perform non-blocking HTTP health checks on source URLs."""
        test_records = records[:sample_size] if sample_size else records
        results = []
        healthy_count = 0
        warning_count = 0

        logger.info("Executing URL health check on %d source URLs...", len(test_records))

        with httpx.Client(timeout=8.0, follow_redirects=True, headers={"User-Agent": "AI-Resource-Library-Audit/1.0"}) as client:
            for r in test_records:
                url = r["source_url"]
                res_id = r["id"]
                try:
                    resp = client.get(url)
                    if resp.status_code in [200, 301, 302, 307, 308]:
                        healthy_count += 1
                        results.append({"id": res_id, "url": url, "status": resp.status_code, "health": "HEALTHY"})
                    else:
                        warning_count += 1
                        results.append({"id": res_id, "url": url, "status": resp.status_code, "health": "WARNING"})
                except Exception as err:
                    warning_count += 1
                    results.append({"id": res_id, "url": url, "status": "ERROR", "health": "WARNING", "error": str(err)})

        return {
            "passed": True,  # Non-blocking: warnings are logged without failing build
            "total_checked": len(test_records),
            "healthy_count": healthy_count,
            "warning_count": warning_count,
            "details": results,
        }

    def run_full_audit(self, check_urls: bool = False) -> Dict[str, Any]:
        """Execute complete quality control audit across all gates."""
        logger.info("Starting comprehensive Quality Assurance Audit...")
        records = self.load_inventory()

        audit_results = {
            "deduplication": self.check_deduplication(records),
            "metadata_completeness": self.check_metadata_completeness(records),
            "file_assets": self.check_file_assets(records),
            "copyright_and_summaries": self.check_copyright_and_summaries(records),
            "markdown_links": self.check_markdown_relative_links(),
            "web_portal": self.check_web_portal(),
            "master_pdf": self.check_master_pdf(),
        }

        if check_urls:
            audit_results["url_health"] = self.check_url_health(records)

        # Compute overall success
        all_passed = all(v.get("passed", False) for v in audit_results.values())
        audit_results["overall_passed"] = all_passed
        audit_results["total_cataloged"] = len(records)

        logger.info("Audit finished. Overall status: %s", "PASS" if all_passed else "FAIL")
        return audit_results
