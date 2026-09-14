"""Master Index Generator (MASTER_INDEX.md).

Compiles all cataloged educational resources into an organized,
hierarchically numbered directory with summary links, source URLs, and metadata.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from src.config import INVENTORY_DIR, MASTER_INDEX_PATH

ORDERED_CATEGORIES = [
    ("1. Getting Started", "Getting Started", "Core AI foundations, beginner roadmaps, usage limits, and setup guides."),
    ("2. Claude Code", "Claude Code", "Agentic coding in the terminal, CLI commands, agent architectures, and testing hooks."),
    ("3. Tools & Integrations", "Tools & Integrations", "MCP connectors, multi-tool pipelines, design stacks, and scrapers."),
    ("4. Prompts & Skills", "Prompts & Skills", "Context engineering, custom skill creation, prompt templates, and security."),
    ("5. Building & Monetising", "Building & Monetising", "Launching micro-SaaS, agencies, digital products, and client acquisition."),
    ("6. AI Automation", "AI Automation", "Scheduled routines, process automation, background workflows, and lead capture."),
    ("7. AI Agents", "AI Agents", "Autonomous workflows, agentic teams, and multi-model collaboration."),
    ("8. AI Business", "AI Business", "Commercial models, ROI optimization, operations, and enterprise efficiency."),
    ("9. AI Coding", "AI Coding", "Vibe coding, automated verification, plugin ecosystems, and error recovery."),
    ("10. AI Marketing", "AI Marketing", "Content pillars, ad management, copywriting, and market intelligence."),
    ("11. AI Productivity", "AI Productivity", "Daily acceleration, memory architecture, and personal workflow management."),
    ("12. Other Discovered Categories", "Other Discovered Categories", "Supplemental tools, specialized playbooks, and emerging guides."),
]


class MasterIndexGenerator:
    """Generates the publication-grade MASTER_INDEX.md file."""

    def __init__(self, inventory_path: Path = None, output_path: Path = None):
        self.inventory_path = inventory_path or (INVENTORY_DIR / "master_inventory.json")
        self.output_path = output_path or MASTER_INDEX_PATH

    def load_inventory(self) -> List[Dict[str, Any]]:
        """Load normalized inventory records."""
        if not self.inventory_path.exists():
            raise FileNotFoundError(f"Inventory not found: {self.inventory_path}")
        with open(self.inventory_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate_markdown(self, records: List[Dict[str, Any]]) -> str:
        """Construct the complete Markdown index string."""
        total_count = len(records)
        lines = [
            "# AI Resource Library — Master Index",
            "",
            "> **Comprehensive Offline Catalog & Navigation Directory**  ",
            f"> **Total Cataloged Resources:** {total_count}  ",
            "> **Publication:** Personal Educational AI Resource Library  ",
            "> **Compliance Status:** 100% Fair Use & Personal Reference (All guides cataloged with original summaries)  ",
            "",
            "---",
            "",
            "## Table of Contents",
            "",
        ]

        # Generate ToC links
        for header, _, _ in ORDERED_CATEGORIES:
            slug_anchor = header.lower().replace(" ", "-").replace(".", "").replace("&", "")
            lines.append(f"- [{header}](#{slug_anchor})")
        lines.append("- [Complete Alphabetical & Numeric Lookup Table](#complete-alphabetical--numeric-lookup-table)")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Group records by category and subcategory
        records_by_category: Dict[str, List[Dict[str, Any]]] = {}
        for r in records:
            cat = r["category"]
            records_by_category.setdefault(cat, []).append(r)

        # Cross-categorization lookup for specialized domains 6-11
        specialized_filters = {
            "AI Automation": lambda r: "automation" in r["subcategory"].lower() or any("automat" in t.lower() for t in r.get("topics", [])),
            "AI Agents": lambda r: "agent" in r["subcategory"].lower() or any("agent" in t.lower() for t in r.get("topics", [])),
            "AI Business": lambda r: "business" in r["subcategory"].lower() or "monetisation" in r["category"].lower(),
            "AI Coding": lambda r: "claude code" in r["category"].lower() or "testing" in r["subcategory"].lower() or "cli" in r["subcategory"].lower(),
            "AI Marketing": lambda r: "marketing" in r["subcategory"].lower() or any("marketing" in t.lower() for t in r.get("topics", [])),
            "AI Productivity": lambda r: "usage" in r["subcategory"].lower() or "routine" in r["subcategory"].lower() or any("productivity" in t.lower() for t in r.get("topics", [])),
        }

        # Render each section
        for header, cat_key, description in ORDERED_CATEGORIES:
            lines.append(f"## {header}")
            lines.append(f"*{description}*")
            lines.append("")

            # Match items
            matched = []
            if cat_key in records_by_category:
                matched = records_by_category[cat_key]
            elif cat_key in specialized_filters:
                filter_fn = specialized_filters[cat_key]
                matched = [r for r in records if filter_fn(r)]

            if not matched:
                lines.append("> *No primary guides directly under this header. See subcategory cross-references above.*")
                lines.append("")
                continue

            lines.append(f"**Found {len(matched)} guides:**")
            lines.append("")
            lines.append("| ID | Title | Difficulty | Subcategory | Summary | Cached Page |")
            lines.append("|---|---|---|---|---|---|")

            for item in matched:
                res_id = item["id"]
                title = item["title"]
                diff = item["difficulty"]
                subcat = item.get("subcategory", "General")
                summary_link = f"[Read Summary](summaries/{res_id}.md)"
                cached_link = f"[Cached Webpage]({item.get('local_html')})" if item.get("local_html") else "N/A"

                lines.append(f"| **{res_id}** | {title} | `{diff}` | {subcat} | {summary_link} | {cached_link} |")

            lines.append("")

            # Detail section for each item
            for item in matched:
                res_id = item["id"]
                title = item["title"]
                desc = item.get("description", "")
                tools = ", ".join(item.get("ai_tools", [])) or "None listed"
                topics = ", ".join(item.get("topics", [])) or "General"
                local_asset = item.get("local_file") or "None (Web Only Guide)"
                cached_asset = f"[Cached Webpage]({item.get('local_html')})" if item.get("local_html") else "N/A"

                lines.append(f"### {res_id}: {title}")
                lines.append(f"- **Category:** {item['category']} ({item.get('subcategory', 'General')})")
                lines.append(f"- **Difficulty:** {item['difficulty']}")
                lines.append(f"- **Description:** {desc}")
                lines.append(f"- **AI Tools:** {tools}")
                lines.append(f"- **Topics:** {topics}")
                lines.append(f"- **Local Reference:** `{local_asset}`")
                lines.append(f"- **Links:** [Structured Analytical Summary](summaries/{res_id}.md) | {cached_asset}")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Complete Lookup Table
        lines.append("## Complete Alphabetical & Numeric Lookup Table")
        lines.append("")
        lines.append("| ID | Title | Category | Difficulty | Key Tools | Summary |")
        lines.append("|---|---|---|---|---|---|")
        for item in sorted(records, key=lambda x: x["id"]):
            res_id = item["id"]
            title = item["title"]
            cat = item["category"]
            diff = item["difficulty"]
            tools = ", ".join(item.get("ai_tools", [])[:3]) or "N/A"
            summary_link = f"[`{res_id}.md`](summaries/{res_id}.md)"
            lines.append(f"| **{res_id}** | {title} | {cat} | {diff} | {tools} | {summary_link} |")

        lines.append("")
        return "\n".join(lines)

    def write_file(self) -> Path:
        """Load records, generate markdown, and write to MASTER_INDEX.md."""
        records = self.load_inventory()
        content = self.generate_markdown(records)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(content, encoding="utf-8")
        return self.output_path
