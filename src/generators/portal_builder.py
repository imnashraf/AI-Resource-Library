"""Offline Web Portal Builder (library.html).

Compiles all inventory metadata and structured analytical summaries into a
single, standalone, zero-dependency offline web application that operates
seamlessly across desktop browsers via file:// protocol without any external CDN calls.
"""

import base64
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import (
    INVENTORY_DIR,
    PORTAL_HTML_PATH,
    PROJECT_ROOT,
    SUMMARIES_DIR,
)

logger = logging.getLogger("portal.builder")


class PortalBuilder:
    """Compiles the standalone zero-dependency library.html offline portal."""

    def __init__(
        self,
        inventory_path: Optional[Path] = None,
        summaries_dir: Optional[Path] = None,
        template_path: Optional[Path] = None,
        output_path: Optional[Path] = None,
    ):
        self.inventory_path = inventory_path or (INVENTORY_DIR / "master_inventory.json")
        self.summaries_dir = summaries_dir or SUMMARIES_DIR
        self.template_path = template_path or (PROJECT_ROOT / "src" / "templates" / "portal.html")
        self.output_path = output_path or PORTAL_HTML_PATH

    def load_dataset(self) -> List[Dict[str, Any]]:
        """Load inventory records and inject corresponding summary markdown."""
        if not self.inventory_path.exists():
            raise FileNotFoundError(f"Inventory not found at: {self.inventory_path}")

        with open(self.inventory_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        enriched_records = []
        for r in records:
            item = dict(r)
            res_id = item.get("id", "")
            summary_file = self.summaries_dir / f"{res_id}.md"

            if summary_file.exists():
                try:
                    item["summary_markdown"] = summary_file.read_text(encoding="utf-8")
                except Exception as err:
                    logger.warning("Could not read summary for %s: %s", res_id, err)
                    item["summary_markdown"] = item.get("description", "")
            else:
                item["summary_markdown"] = item.get("description", "")

            enriched_records.append(item)

        return enriched_records

    def build_portal_html(self, records: List[Dict[str, Any]]) -> str:
        """Read template and inject inlined JSON dataset and metadata."""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Portal template not found at: {self.template_path}")

        template_content = self.template_path.read_text(encoding="utf-8")

        # Serialize dataset to JSON, safely escaping closing script tags to prevent HTML parser break
        json_payload = json.dumps(records, ensure_ascii=False)
        safe_json_payload = json_payload.replace("</script>", "<\\/script>")

        # Inject inlined dataset into template placeholder
        if "__LIBRARY_DATA_JSON__" not in template_content:
            raise ValueError("Template is missing __LIBRARY_DATA_JSON__ placeholder.")

        rendered = template_content.replace("__LIBRARY_DATA_JSON__", safe_json_payload)

        # Inject inlined user avatar if available
        avatar_b64 = self.get_user_avatar_base64()
        rendered = rendered.replace("__USER_AVATAR_B64__", avatar_b64)

        return rendered

    def get_user_avatar_base64(self) -> str:
        """Find local avatar image in assets and encode as base64 data URL."""
        candidate_paths = [
            self.output_path.parent / "assets" / "avatar.jpg",
            self.output_path.parent / "assets" / "avatar.png",
            self.output_path.parent / "assets" / "profile.jpg",
            self.output_path.parent / "assets" / "profile.png",
            PROJECT_ROOT / "ai-resource-library" / "assets" / "avatar.jpg",
            PROJECT_ROOT / "ai-resource-library" / "assets" / "avatar.png",
        ]
        for p in candidate_paths:
            if p.exists():
                try:
                    mime = "image/jpeg" if p.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
                    encoded = base64.b64encode(p.read_bytes()).decode("utf-8")
                    return f"data:{mime};base64,{encoded}"
                except Exception as err:
                    logger.warning("Could not encode avatar at %s: %s", p, err)
        return ""

    def write_portal(self) -> Path:
        """Build and write the final library.html file."""
        records = self.load_dataset()
        logger.info("Loaded %d enriched records for offline portal.", len(records))

        html_content = self.build_portal_html(records)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(html_content, encoding="utf-8")

        logger.info("Successfully wrote offline web portal to: %s (%d bytes)", self.output_path, len(html_content))
        return self.output_path


def main():
    """CLI runner for portal compilation."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    builder = PortalBuilder()
    output_file = builder.write_portal()
    print(f"\n[Phase 6] Successfully generated offline web portal:\n  -> {output_file}")


if __name__ == "__main__":
    main()
