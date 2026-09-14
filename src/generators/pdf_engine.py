"""Offline Master Reference PDF Compilation Engine (AI_RESOURCE_LIBRARY_MASTER.pdf).

Generates a publication-grade, offline master reference manual using ReportLab.
Includes cover page, executive front matter, table of contents, learning roadmaps,
category directories, uniform 2-page resource profile cards, and cross-reference indexes.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.config import (
    DOCUMENTS_DIR,
    INVENTORY_DIR,
    MASTER_PDF_PATH,
    PROJECT_ROOT,
    SUMMARIES_DIR,
)
from src.generators.pdf_styles import (
    BORDER_COLOR,
    BORDER_SUBTLE,
    CARD_BG,
    DIFF_COLORS,
    MARGIN_BOTTOM,
    MARGIN_LEFT,
    MARGIN_RIGHT,
    MARGIN_TOP,
    PAGE_HEIGHT,
    PAGE_WIDTH,
    PRINTABLE_WIDTH,
    TEAL_BORDER,
    TEAL_DARK,
    TEAL_LIGHT,
    TEAL_PRIMARY,
    TEXT_DARK,
    TEXT_LIGHT,
    TEXT_MUTED,
    WARM_BG,
    WHITE,
    BookmarkFlowable,
    MasterNumberedCanvas,
    SectionHeaderFlowable,
    get_pdf_styles,
)
from src.generators.roadmap_generator import ROADMAP_TRACKS, TRACK_DURATIONS

logger = logging.getLogger("pdf.engine")


def sanitize_text_for_xml(text: str) -> str:
    """Sanitize raw text and convert markdown syntax to ReportLab XML paragraph tags."""
    if not text:
        return ""

    # Normalize unicode symbols that may cause encoding issues in standard Helvetica
    replacements = {
        "→": "-&gt;",
        "←": "&lt;-",
        "↔": "&lt;-&gt;",
        "—": "--",
        "–": "-",
        "\u2011": "-",  # non-breaking hyphen
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "--",
        "“": "\"",
        "”": "\"",
        "\u201c": "\"",
        "\u201d": "\"",
        "‘": "'",
        "’": "'",
        "\u2018": "'",
        "\u2019": "'",
        "•": "&bull;",
        "…": "...",
        "\u2026": "...",
        "\u00a0": " ",   # non-breaking space
        "✦": "*",
        "✔": "[x]",
        "✓": "[x]",
        "✖": "[ ]",
        "&": "&amp;",  # will be handled carefully below
    }

    # Step 1: Escape ampersands that are not already entities
    s = re.sub(r"&(?!(amp|lt|gt|quot|apos|bull);)", "&amp;", text)

    # Step 2: Escape < and >
    s = s.replace("<", "&lt;").replace(">", "&gt;")

    # Step 3: Replace unicode symbols
    for k, v in replacements.items():
        if k != "&":
            s = s.replace(k, v)

    # Step 4: Markdown bold **text** -> <b>text</b>
    s = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", s)

    # Step 5: Markdown italic *text* -> <i>\1</i>
    s = re.sub(r"\*(.*?)\*", r"<i>\1</i>", s)

    # Step 6: Markdown inline code `code` -> Courier bold
    s = re.sub(r"`([^`]+)`", r'<b><font name="Courier">\1</font></b>', s)

    return s


def parse_summary_sections(md_text: str) -> Dict[str, str]:
    """Parse the 8 numbered section headers from a summary markdown file."""
    sections: Dict[str, str] = {}
    current_key = "header"
    current_lines: List[str] = []

    pattern = re.compile(r"^##\s*(\d)\.\s*(.*)$")

    for line in md_text.splitlines():
        m = pattern.match(line.strip())
        if m:
            sections[current_key] = "\n".join(current_lines).strip()
            current_key = f"section_{m.group(1)}"
            current_lines = []
        else:
            current_lines.append(line)

    sections[current_key] = "\n".join(current_lines).strip()
    return sections


def text_to_paragraphs(raw_text: str, style, bullet_style, max_chars: Optional[int] = None) -> List[Any]:
    """Convert raw text or bullet list into a sequence of ReportLab Paragraph objects."""
    if not raw_text:
        return [Paragraph("<i>Information pending or summarized in companion files.</i>", style)]

    if max_chars and len(raw_text) > max_chars:
        raw_text = raw_text[:max_chars] + "... [consult complete summary for extended details]"

    flowables = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Check for bullet items
        bullet_match = re.match(r"^[-*]\s+(.*)$", line)
        if bullet_match:
            clean_item = sanitize_text_for_xml(bullet_match.group(1))
            flowables.append(Paragraph(f"&bull; {clean_item}", bullet_style))
        else:
            # Check for subheadings inside section (### Heading)
            if line.startswith("### "):
                clean_h = sanitize_text_for_xml(line[4:].strip())
                flowables.append(Paragraph(f"<b>{clean_h}</b>", style))
            else:
                clean_p = sanitize_text_for_xml(line)
                flowables.append(Paragraph(clean_p, style))

    return flowables or [Paragraph("<i>Content available in summary file.</i>", style)]


class MasterPdfCompiler:
    """Compiles the complete AI_RESOURCE_LIBRARY_MASTER.pdf document."""

    def __init__(
        self,
        inventory_path: Optional[Path] = None,
        summaries_dir: Optional[Path] = None,
        output_path: Optional[Path] = None,
    ):
        self.inventory_path = inventory_path or (INVENTORY_DIR / "master_inventory.json")
        self.summaries_dir = summaries_dir or SUMMARIES_DIR
        self.output_path = output_path or MASTER_PDF_PATH
        self.styles = get_pdf_styles()

    def load_dataset(self) -> List[Dict[str, Any]]:
        """Load inventory records and attach corresponding summary markdown."""
        if not self.inventory_path.exists():
            raise FileNotFoundError(f"Inventory not found: {self.inventory_path}")

        with open(self.inventory_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        enriched = []
        for r in records:
            item = dict(r)
            res_id = item.get("id", "")
            sum_file = self.summaries_dir / f"{res_id}.md"
            if sum_file.exists():
                try:
                    item["summary_content"] = sum_file.read_text(encoding="utf-8")
                except Exception as err:
                    logger.warning("Could not read summary for %s: %s", res_id, err)
                    item["summary_content"] = item.get("description", "")
            else:
                item["summary_content"] = item.get("description", "")
            enriched.append(item)

        # Sort stably by ID (AI-001 through AI-071)
        enriched.sort(key=lambda x: x["id"])
        return enriched

    def build_cover_page(self) -> List[Any]:
        """Construct the elegant cover page."""
        story = [
            BookmarkFlowable("cover", "Cover Page", level=0),
            SectionHeaderFlowable("Cover Page", key="", level=0),
            Spacer(1, 20),
        ]

        # Top Decorative Color Block
        banner_content = [
            [Paragraph("AI RESOURCE LIBRARY", self.styles["CoverTitle"])],
            [Paragraph("MASTER REFERENCE MANUAL &amp; CURRICULUM DIRECTORY", self.styles["CoverSubtitle"])],
            [Spacer(1, 15)],
            [Paragraph("<b>OFFLINE REFERENCE EDITION</b> &bull; VERSION 1.0.0 &bull; SEPTEMBER 2026", self.styles["CoverMeta"])],
            [Paragraph("A Systematic Personal Knowledge Base for AI Fluency, Claude Code, and Modern Agentic Architecture", self.styles["CoverMeta"])],
        ]
        banner_table = Table(banner_content, colWidths=[PRINTABLE_WIDTH])
        banner_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), TEAL_PRIMARY),
            ("LEFTPADDING", (0, 0), (-1, -1), 24),
            ("RIGHTPADDING", (0, 0), (-1, -1), 24),
            ("TOPPADDING", (0, 0), (-1, -1), 32),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 32),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(banner_table)
        story.append(Spacer(1, 40))

        # Middle Metadata Cards
        features_data = [
            [
                Paragraph("<b>71 Comprehensive Resources</b><br/><font color='#555555'>Getting Started, Claude Code, Tools, Prompts &amp; Monetisation</font>", self.styles["Body"]),
                Paragraph("<b>8 Curated Learning Roadmaps</b><br/><font color='#555555'>Prerequisite-ordered paths from Beginner to AI Developer</font>", self.styles["Body"]),
            ],
            [
                Paragraph("<b>Structured 2-Page Profiles</b><br/><font color='#555555'>Detailed takeaways, tools, workflows, and personal notes space</font>", self.styles["Body"]),
                Paragraph("<b>100% Offline Air-Gapped Ready</b><br/><font color='#555555'>Self-contained publication with zero external CDN dependencies</font>", self.styles["Body"]),
            ],
        ]
        feat_table = Table(features_data, colWidths=[PRINTABLE_WIDTH / 2.0, PRINTABLE_WIDTH / 2.0])
        feat_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), WARM_BG),
            ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("LEFTPADDING", (0, 0), (-1, -1), 16),
            ("RIGHTPADDING", (0, 0), (-1, -1), 16),
            ("TOPPADDING", (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ]))
        story.append(feat_table)
        story.append(Spacer(1, 60))

        # Bottom Attribution & Notice Block
        bottom_box = [
            [Paragraph("<b>Publication &amp; Compilation:</b> AI Resource Library Editorial", self.styles["Body"])],
            [Paragraph("<b>Compliance &amp; Fair Use:</b> Strictly compiled for private non-commercial study and personal reference. All guide summaries are original analytical syntheses. Original full articles remain the property of their author.", self.styles["LegalNotice"])],
        ]
        bottom_table = Table(bottom_box, colWidths=[PRINTABLE_WIDTH])
        bottom_table.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LINEBEFORE", (0, 0), (0, -1), 3, TEAL_PRIMARY),
        ]))
        story.append(bottom_table)

        story.append(PageBreak())
        return story

    def build_front_matter(self) -> List[Any]:
        """Construct executive front matter, copyright disclaimers, and user navigation guide."""
        story = [
            BookmarkFlowable("front_matter", "Part I: Executive Front Matter", level=0),
            SectionHeaderFlowable("Executive Front Matter", key="", level=0),
            Paragraph("Part I: Executive Front Matter &amp; Navigation Guide", self.styles["PartTitle"]),
            HRFlowable(width="100%", thickness=1.5, color=TEAL_PRIMARY, spaceBefore=4, spaceAfter=14),
        ]

        # Executive Statement
        story.append(Paragraph("1. Executive Mission &amp; Purpose", self.styles["SectionHeading"]))
        story.append(Paragraph(
            "The <b>AI Resource Library</b> is an offline personal intelligence repository and structured "
            "reference manual compiling 71 educational guides. The goal of this publication is to provide an organized, searchable, and "
            "offline-accessible reference manual for mastering AI workflows, prompt engineering, Claude Code CLI "
            "architectures, tool integrations, and AI-enabled commercial services.",
            self.styles["BodyLead"]
        ))
        story.append(Paragraph(
            "In modern professional environments where deep technical work requires uninterrupted focus, "
            "this manual provides an air-gapped companion that can be navigated on local hardware without internet "
            "access, external API calls, or cloud dependencies.",
            self.styles["Body"]
        ))

        # Copyright & Fair Use Statement Box
        disclaimer_text = (
            "<b>STATUTORY FAIR USE &amp; INTELLECTUAL PROPERTY NOTICE:</b><br/>"
            "This document is compiled strictly for personal, private educational study and non-commercial reference "
            "under Title 17, Section 107 of the United States Copyright Act (Fair Use). "
            "All resource profiles contained in Part V represent original analytical syntheses, transformative "
            "summaries, and pedagogical evaluations. Original articles, proprietary videos, and protected commercial "
            "assets are not reproduced verbatim herein and remain the intellectual property of their respective creators."
        )
        disc_table = Table([[Paragraph(disclaimer_text, self.styles["Body"])]], colWidths=[PRINTABLE_WIDTH])
        disc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), TEAL_LIGHT),
            ("BOX", (0, 0), (-1, -1), 1, TEAL_BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(Spacer(1, 6))
        story.append(disc_table)
        story.append(Spacer(1, 14))

        # Navigation Guide
        story.append(Paragraph("2. How to Navigate This Reference Manual", self.styles["SectionHeading"]))
        story.append(Paragraph(
            "This volume is arranged into six structured parts designed to support both broad curriculum study "
            "and immediate reference lookup:",
            self.styles["Body"]
        ))

        nav_points = [
            ("Part I: Front Matter", "Mission, copyright parameters, navigation guidelines, and core concepts."),
            ("Part II: Table of Contents", "Hierarchical roadmap and section index with page pointers."),
            ("Part III: Learning Roadmaps", "8 curated progression paths (Paths A through H) sequenced through 5 milestone stages."),
            ("Part IV: Category Directories", "High-level inventory summary tables grouped by canonical category."),
            ("Part V: Comprehensive Resource Profiles", "Uniform 2-page detailed profiles for all 71 guides with learning takeaways, key tools, workflows, and personal notes space."),
            ("Part VI: Master Indexes", "Complete alphabetical directory and tool-based cross-reference lookup."),
        ]
        for title, desc in nav_points:
            story.append(Paragraph(f"&bull; <b>{title}:</b> {desc}", self.styles["BulletText"]))

        story.append(Spacer(1, 10))
        story.append(Paragraph("3. The 5-Stage Milestone Progression Architecture", self.styles["SectionHeading"]))
        story.append(Paragraph(
            "Every learning roadmap in Part III follows a standardized 5-stage milestone architecture to ensure "
            "sustainable skill accumulation without cognitive overload:",
            self.styles["Body"]
        ))

        milestones_box = [
            [
                Paragraph("<b>1. START HERE</b><br/><font color='#555555'>Foundation &amp; Setup</font>", self.styles["TableCellBold"]),
                Paragraph("<b>2. NEXT</b><br/><font color='#555555'>Core Practices</font>", self.styles["TableCellBold"]),
                Paragraph("<b>3. INTERMEDIATE</b><br/><font color='#555555'>Workflows &amp; Automation</font>", self.styles["TableCellBold"]),
                Paragraph("<b>4. ADVANCED</b><br/><font color='#555555'>Architectural Hardening</font>", self.styles["TableCellBold"]),
                Paragraph("<b>5. CAPSTONE</b><br/><font color='#555555'>Production System</font>", self.styles["TableCellBold"]),
            ]
        ]
        m_table = Table(milestones_box, colWidths=[PRINTABLE_WIDTH / 5.0] * 5)
        m_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), WARM_BG),
            ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(m_table)

        story.append(PageBreak())
        return story

    def build_table_of_contents(self, records: List[Dict[str, Any]]) -> List[Any]:
        """Construct the hierarchical Table of Contents."""
        story = [
            BookmarkFlowable("toc", "Part II: Table of Contents", level=0),
            SectionHeaderFlowable("Table of Contents", key="", level=0),
            Paragraph("Part II: Table of Contents", self.styles["PartTitle"]),
            HRFlowable(width="100%", thickness=1.5, color=TEAL_PRIMARY, spaceBefore=4, spaceAfter=14),
            Paragraph(
                "This publication contains 71 individual resource profiles and 8 structured learning roadmaps. "
                "All section titles and resource IDs correspond to interactive bookmarks in the PDF document outline.",
                self.styles["Body"]
            ),
            Spacer(1, 10),
        ]

        toc_data = [
            ("Part I: Executive Front Matter &amp; Navigation Guide", "Overview, Copyright Notice, 5-Stage Progression Model"),
            ("Part II: Table of Contents", "Overview of Volume Sections &amp; Roadmap Directory"),
            ("Part III: Systematic Learning Roadmaps (Paths A through H)", "8 Progressive Curricula: Beginner, Power User, Developer, Agency, etc."),
            ("Part IV: Category Directories", "1. Getting Started  •  2. Claude Code  •  3. Tools  •  4. Prompts  •  5. Monetising"),
            ("Part V: Comprehensive Resource Profiles (Main Body)", "Detailed 2-Page Profiles for Guides AI-001 through AI-071"),
            ("Part VI: Master Cross-Reference Indexes", "Complete Alphabetical Index &amp; Tool Lookup Directory"),
        ]

        table_rows = []
        for part_title, part_desc in toc_data:
            table_rows.append([
                Paragraph(f"<b>{part_title}</b>", self.styles["TableCellBold"]),
                Paragraph(f"<font color='#555555'>{part_desc}</font>", self.styles["TableCell"]),
            ])

        toc_table = Table(table_rows, colWidths=[200, 340])
        toc_table.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(toc_table)
        story.append(Spacer(1, 15))

        # Roadmap Quick Index
        story.append(Paragraph("Curriculum Paths Quick Index (Part III)", self.styles["SectionHeading"]))
        roadmap_rows = []
        for track in ROADMAP_TRACKS:
            pid = track["path_id"]
            title = track["title"]
            badge = track["badge"]
            dur, _ = TRACK_DURATIONS.get(pid, ("3–4 weeks", []))
            roadmap_rows.append([
                Paragraph(f"<b>{pid}: {title}</b>", self.styles["TableCellBold"]),
                Paragraph(f"<font color='#1A7A6A'>{badge}</font>", self.styles["TableCell"]),
                Paragraph(f"<font color='#555555'>{dur}</font>", self.styles["TableCell"]),
            ])

        r_table = Table(roadmap_rows, colWidths=[180, 160, 200])
        r_table.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(r_table)

        story.append(PageBreak())
        return story

    def build_roadmaps_section(self) -> List[Any]:
        """Construct Part III: Systematic Learning Roadmaps (Paths A through H)."""
        story = [
            BookmarkFlowable("roadmaps", "Part III: Learning Roadmaps", level=0),
            SectionHeaderFlowable("Learning Roadmaps", key="", level=0),
            Paragraph("Part III: Systematic Learning Roadmaps", self.styles["PartTitle"]),
            HRFlowable(width="100%", thickness=1.5, color=TEAL_PRIMARY, spaceBefore=4, spaceAfter=14),
            Paragraph(
                "Eight specialized curricula designed to guide practitioners through progressive skill accumulation. "
                "Each path progresses through five rigorous milestones from initial setup to production capstone.",
                self.styles["BodyLead"]
            ),
            Spacer(1, 10),
        ]

        for idx, track in enumerate(ROADMAP_TRACKS, 1):
            pid = track["path_id"]
            title = track["title"]
            badge = track["badge"]
            desc = track["description"]
            aud = track["audience"]
            track_dur, stage_durs = TRACK_DURATIONS.get(pid, ("3–4 weeks (20–30 hours total)", ["3–4 hours"] * 5))

            story.append(BookmarkFlowable(f"track_{pid}", f"{pid}: {title}", level=1))
            story.append(Paragraph(f"{pid}: {title}", self.styles["SectionHeading"]))
            story.append(Paragraph(
                f"<b>Focus:</b> {badge} &nbsp;|&nbsp; <b>Ideal Audience:</b> {aud} &nbsp;|&nbsp; <b>Estimated Duration:</b> {track_dur}",
                self.styles["CardMeta"]
            ))
            story.append(Paragraph(desc, self.styles["Body"]))
            story.append(Spacer(1, 4))

            # Milestone Table
            m_header = [
                Paragraph("<b>Milestone</b>", self.styles["TableHeader"]),
                Paragraph("<b>ID &amp; Title</b>", self.styles["TableHeader"]),
                Paragraph("<b>Diff.</b>", self.styles["TableHeader"]),
                Paragraph("<b>Est. Time</b>", self.styles["TableHeader"]),
                Paragraph("<b>Core Takeaway</b>", self.styles["TableHeader"]),
            ]
            m_rows = [m_header]

            for s_idx, s in enumerate(track["stages"]):
                stage_name = s["stage"]
                res_id = s["id"]
                res_title = s["title"]
                diff = s["difficulty"]
                takeaway = s["key_takeaway"]
                time_est = stage_durs[s_idx] if s_idx < len(stage_durs) else "3–4 hours"

                m_rows.append([
                    Paragraph(f"<b>{stage_name}</b>", self.styles["TableCellBold"]),
                    Paragraph(f"<b>{res_id}</b>: {res_title}", self.styles["TableCell"]),
                    Paragraph(diff, self.styles["TableCell"]),
                    Paragraph(time_est, self.styles["TableCell"]),
                    Paragraph(takeaway, self.styles["TableCell"]),
                ])

            t = Table(m_rows, colWidths=[95, 145, 55, 65, 180])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), TEAL_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(t)
            story.append(Spacer(1, 14))

            # Page break every 2 tracks to keep formatting clean
            if idx % 2 == 0 and idx < len(ROADMAP_TRACKS):
                story.append(PageBreak())

        story.append(PageBreak())
        return story

    def build_category_directories(self, records: List[Dict[str, Any]]) -> List[Any]:
        """Construct Part IV: Category Directories with high-level tables."""
        story = [
            BookmarkFlowable("categories", "Part IV: Category Directories", level=0),
            SectionHeaderFlowable("Category Directories", key="", level=0),
            Paragraph("Part IV: Category Directories", self.styles["PartTitle"]),
            HRFlowable(width="100%", thickness=1.5, color=TEAL_PRIMARY, spaceBefore=4, spaceAfter=14),
            Paragraph(
                "High-level index of all 71 guides arranged across the 5 canonical project categories. "
                "Use this section to quickly identify all available modules within a specific domain.",
                self.styles["BodyLead"]
            ),
            Spacer(1, 10),
        ]

        # Group records by category
        cat_map: Dict[str, List[Dict[str, Any]]] = {}
        for r in records:
            cat_map.setdefault(r["category"], []).append(r)

        category_order = [
            ("Getting Started", "Core foundations, beginner setup guides, usage optimization, and initial configuration."),
            ("Claude Code", "Terminal agentic coding, CLI commands, agent topologies, multi-model setups, and verification."),
            ("Tools & Integrations", "MCP connectors, external tooling, browser automation, scrapers, and audio pipelines."),
            ("Prompts & Skills", "Context engineering, custom skill creation, prompt optimization, and security audits."),
            ("Building & Monetising", "Micro-SaaS playbooks, agency services, digital products, cold outreach, and startup stacks."),
        ]

        for cat_name, cat_desc in category_order:
            cat_records = cat_map.get(cat_name, [])
            story.append(BookmarkFlowable(f"cat_{cat_name.lower().replace(' ', '_')}", cat_name, level=1))
            story.append(Paragraph(f"{cat_name} ({len(cat_records)} Guides)", self.styles["SectionHeading"]))
            story.append(Paragraph(f"<i>{cat_desc}</i>", self.styles["BodyMuted"]))
            story.append(Spacer(1, 4))

            # Table of guides in category
            header = [
                Paragraph("<b>ID</b>", self.styles["TableHeader"]),
                Paragraph("<b>Title</b>", self.styles["TableHeader"]),
                Paragraph("<b>Difficulty</b>", self.styles["TableHeader"]),
                Paragraph("<b>Subcategory</b>", self.styles["TableHeader"]),
                Paragraph("<b>Key Tools</b>", self.styles["TableHeader"]),
            ]
            rows = [header]

            for r in cat_records:
                tools_str = ", ".join(r.get("ai_tools", [])[:3]) or "None listed"
                rows.append([
                    Paragraph(f"<b>{r['id']}</b>", self.styles["TableCellBold"]),
                    Paragraph(r["title"], self.styles["TableCell"]),
                    Paragraph(r["difficulty"], self.styles["TableCell"]),
                    Paragraph(r.get("subcategory", "General"), self.styles["TableCell"]),
                    Paragraph(tools_str, self.styles["TableCell"]),
                ])

            table = Table(rows, colWidths=[45, 195, 75, 105, 120])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), TEAL_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(table)
            story.append(Spacer(1, 14))

        story.append(PageBreak())
        return story

    def build_resource_profiles(self, records: List[Dict[str, Any]]) -> List[Any]:
        """Construct Part V: Comprehensive Resource Profiles.
        
        Every resource is laid out as a predictable, structured 2-page card:
        - Page 1: Metadata, Overview, What You Learn, Why It Matters, Target Audience.
        - Page 2: Key Concepts, Tools, Workflows, Notes Area, Source Pointers.
        """
        story = [
            BookmarkFlowable("profiles", "Part V: Resource Profiles", level=0),
            SectionHeaderFlowable("Resource Profiles", key="", level=0),
            Paragraph("Part V: Comprehensive Resource Profiles", self.styles["PartTitle"]),
            HRFlowable(width="100%", thickness=1.5, color=TEAL_PRIMARY, spaceBefore=4, spaceAfter=14),
            Paragraph(
                "This section contains uniform 2-page structured profile cards for each of the 71 cataloged "
                "educational guides. Each card synthesizes learning outcomes, strategic relevance, key tools, "
                "implementation steps, and includes an offline personal notes area.",
                self.styles["BodyLead"]
            ),
            Spacer(1, 15),
        ]

        total_resources = len(records)

        for idx, item in enumerate(records, 1):
            res_id = item["id"]
            title = item["title"]
            category = item["category"]
            subcategory = item.get("subcategory", "General")
            difficulty = item["difficulty"]
            tools_list = ", ".join(item.get("ai_tools", [])) or "None specified"
            topics_list = ", ".join(item.get("topics", [])) or "General"
            summary_raw = item.get("summary_content", "")
            sections = parse_summary_sections(summary_raw)

            # Determine difficulty styling
            diff_style_data = DIFF_COLORS.get(difficulty, DIFF_COLORS["Beginner"])

            # -------------------------------------------------------------
            # CARD PAGE 1: Overview, Objectives & Relevance
            # -------------------------------------------------------------
            story.append(BookmarkFlowable(f"res_{res_id}", f"{res_id}: {title[:45]}", level=1))
            story.append(SectionHeaderFlowable(f"{category} • {res_id}", key="", level=0))

            # Header Top Banner Table
            banner_data = [
                [
                    Paragraph(f"<b>{res_id}</b> &nbsp;|&nbsp; {category} &bull; {subcategory}", self.styles["TableCellBold"]),
                    Paragraph(f"<b>{difficulty.upper()}</b>", self.styles["TableCellBold"]),
                ]
            ]
            banner_table = Table(banner_data, colWidths=[420, 120])
            banner_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), TEAL_LIGHT),
                ("BACKGROUND", (1, 0), (1, 0), diff_style_data["bg"]),
                ("TEXTCOLOR", (0, 0), (0, 0), TEAL_DARK),
                ("TEXTCOLOR", (1, 0), (1, 0), diff_style_data["text"]),
                ("BOX", (0, 0), (-1, -1), 1, TEAL_BORDER),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]))
            story.append(banner_table)
            story.append(Spacer(1, 6))

            # Title
            story.append(Paragraph(f"{res_id}: {sanitize_text_for_xml(title)}", self.styles["CardTitle"]))
            story.append(Spacer(1, 4))

            # Metadata Table Box
            meta_box_data = [
                [
                    Paragraph("<b>Tools &amp; Topics:</b>", self.styles["TableCellBold"]),
                    Paragraph(f"Tools: {sanitize_text_for_xml(tools_list)} &nbsp;|&nbsp; Topics: {sanitize_text_for_xml(topics_list)}", self.styles["TableCell"]),
                ],
                [
                    Paragraph("<b>Format &amp; Access:</b>", self.styles["TableCellBold"]),
                    Paragraph("Comprehensive Offline Educational Guide &amp; Analytical Synthesis", self.styles["TableCell"]),
                ],
            ]
            meta_table = Table(meta_box_data, colWidths=[90, 450])
            meta_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(meta_table)
            story.append(Spacer(1, 8))

            # Section 1: What This Resource Teaches
            story.append(Paragraph("1. What This Resource Teaches", self.styles["CardSectionHeading"]))
            s1_text = sections.get("section_1", item.get("description", ""))
            s1_flowables = text_to_paragraphs(s1_text, self.styles["Body"], self.styles["BulletText"], max_chars=800)
            story.extend(s1_flowables)
            story.append(Spacer(1, 6))

            # Section 2: Why It Matters
            story.append(Paragraph("2. Why It Matters &amp; Strategic Relevance", self.styles["CardSectionHeading"]))
            s2_text = sections.get("section_2", "Strategic efficiency and workflow acceleration.")
            s2_flowables = text_to_paragraphs(s2_text, self.styles["Body"], self.styles["BulletText"], max_chars=500)
            story.extend(s2_flowables)
            story.append(Spacer(1, 6))

            # Section 3: Target Audience
            story.append(Paragraph("3. Target Audience &amp; Ideal Roles", self.styles["CardSectionHeading"]))
            s3_text = sections.get("section_3", "Software engineers, technical operators, and AI enthusiasts.")
            s3_flowables = text_to_paragraphs(s3_text, self.styles["Body"], self.styles["BulletText"], max_chars=350)
            story.extend(s3_flowables)

            # Footer indicator for Page 1
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                f"<font color='#888888'><i>Profile 1 of 2 for {res_id} &bull; Turn page for concepts, workflows, and personal notes.</i></font>",
                self.styles["LegalNotice"]
            ))

            story.append(PageBreak())

            # -------------------------------------------------------------
            # CARD PAGE 2: Concepts, Tools, Workflows & Personal Notes
            # -------------------------------------------------------------
            story.append(SectionHeaderFlowable(f"{category} • {res_id} (Workflows & Notes)", key="", level=0))

            # Page 2 Header Banner
            p2_header = Table([[
                Paragraph(f"<b>{res_id} (Continued)</b> &bull; {sanitize_text_for_xml(title)}", self.styles["TableCellBold"]),
                Paragraph(f"<b>Part V: Profile Card</b>", self.styles["TableCell"]),
            ]], colWidths=[420, 120])
            p2_header.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), WARM_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(p2_header)
            story.append(Spacer(1, 6))

            # Section 4: Key Concepts & Principles
            story.append(Paragraph("4. Key Concepts &amp; Principles", self.styles["CardSectionHeading"]))
            s4_text = sections.get("section_4", "")
            s4_flowables = text_to_paragraphs(s4_text, self.styles["Body"], self.styles["BulletText"], max_chars=550)
            story.extend(s4_flowables)
            story.append(Spacer(1, 6))

            # Section 5: Tools & Technologies Mentioned
            story.append(Paragraph("5. Tools &amp; Technologies Mentioned", self.styles["CardSectionHeading"]))
            s5_text = sections.get("section_5", tools_list)
            s5_flowables = text_to_paragraphs(s5_text, self.styles["Body"], self.styles["BulletText"], max_chars=350)
            story.extend(s5_flowables)
            story.append(Spacer(1, 6))

            # Section 6: Practical Use Cases & Workflows
            story.append(Paragraph("6. Practical Use Cases &amp; Workflows", self.styles["CardSectionHeading"]))
            s6_text = sections.get("section_6", "")
            s6_flowables = text_to_paragraphs(s6_text, self.styles["Body"], self.styles["BulletText"], max_chars=600)
            story.extend(s6_flowables)
            story.append(Spacer(1, 6))

            # Section 7: Prerequisites & Next Steps
            story.append(Paragraph("7. Prerequisites &amp; Recommended Next Steps", self.styles["CardSectionHeading"]))
            s7_text = sections.get("section_7", "None specified.")
            s8_text = sections.get("section_8", "Proceed through current roadmap sequence.")
            combo_next = f"<b>Prerequisites:</b> {s7_text}<br/><b>Next Steps:</b> {s8_text}"
            story.append(Paragraph(sanitize_text_for_xml(combo_next), self.styles["Body"]))
            story.append(Spacer(1, 6))

            # Section 8: Personal Notes & Implementation Ideas Area
            story.append(Paragraph("8. Personal Notes &amp; Implementation Ideas", self.styles["CardSectionHeading"]))
            notes_lines = [
                [Paragraph("<font color='#AAAAAA'>Key takeaway for my workflow:</font>", self.styles["LegalNotice"])],
                [Spacer(1, 10)],
                [HRFlowable(width="100%", thickness=0.4, color=BORDER_COLOR, spaceBefore=2, spaceAfter=2)],
                [Spacer(1, 10)],
                [HRFlowable(width="100%", thickness=0.4, color=BORDER_COLOR, spaceBefore=2, spaceAfter=2)],
            ]
            notes_table = Table(notes_lines, colWidths=[PRINTABLE_WIDTH])
            notes_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(notes_table)
            story.append(Spacer(1, 6))

            # Section 9: Access Reference & Mandatory Fair Use Notice
            local_html_path = item.get("local_html", f"web-pages/{res_id}.html")
            fair_use_text = (
                f"<b>Offline Assets:</b> Analytical Summary: <code>summaries/{res_id}.md</code> &bull; "
                f"Archived Local HTML: <code>{local_html_path}</code><br/>"
                f"<b>Fair Use Compliance Notice:</b> Strictly for private personal study and non-commercial reference. "
                f"Original full text is not reproduced verbatim herein."
            )
            story.append(Paragraph(fair_use_text, self.styles["LegalNotice"]))

            # Explicit page break after page 2
            story.append(PageBreak())

        return story

    def build_indexes_section(self, records: List[Dict[str, Any]]) -> List[Any]:
        """Construct Part VI: Master Cross-Reference Indexes."""
        story = [
            BookmarkFlowable("indexes", "Part VI: Master Indexes", level=0),
            SectionHeaderFlowable("Master Indexes", key="", level=0),
            Paragraph("Part VI: Master Cross-Reference Indexes", self.styles["PartTitle"]),
            HRFlowable(width="100%", thickness=1.5, color=TEAL_PRIMARY, spaceBefore=4, spaceAfter=14),
            Paragraph(
                "Complete alphabetical directory and tool-based cross-reference lookup for all 71 cataloged guides.",
                self.styles["BodyLead"]
            ),
            Spacer(1, 10),
        ]

        # 1. Alphabetical Index (A to Z)
        story.append(BookmarkFlowable("alpha_index", "Alphabetical Resource Index", level=1))
        story.append(Paragraph("1. Complete Alphabetical Resource Index", self.styles["SectionHeading"]))

        sorted_by_title = sorted(records, key=lambda x: x["title"].lower())
        alpha_header = [
            Paragraph("<b>Title</b>", self.styles["TableHeader"]),
            Paragraph("<b>ID</b>", self.styles["TableHeader"]),
            Paragraph("<b>Category</b>", self.styles["TableHeader"]),
            Paragraph("<b>Difficulty</b>", self.styles["TableHeader"]),
        ]
        alpha_rows = [alpha_header]

        for r in sorted_by_title:
            alpha_rows.append([
                Paragraph(r["title"], self.styles["TableCellBold"]),
                Paragraph(r["id"], self.styles["TableCell"]),
                Paragraph(r["category"], self.styles["TableCell"]),
                Paragraph(r["difficulty"], self.styles["TableCell"]),
            ])

        alpha_table = Table(alpha_rows, colWidths=[270, 55, 125, 90])
        alpha_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TEAL_PRIMARY),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(alpha_table)
        story.append(Spacer(1, 15))

        # 2. Tool Cross-Reference Index
        story.append(BookmarkFlowable("tool_index", "AI Tools & Technologies Index", level=1))
        story.append(Paragraph("2. AI Tools &amp; Technologies Index", self.styles["SectionHeading"]))
        story.append(Paragraph(
            "Cross-reference of major AI tools and platforms mapped to their relevant resource guides:",
            self.styles["Body"]
        ))

        # Invert tool mapping
        tool_to_guides: Dict[str, List[str]] = {}
        for r in records:
            for t in r.get("ai_tools", []):
                t_clean = t.strip()
                if t_clean:
                    tool_to_guides.setdefault(t_clean, []).append(r["id"])

        tool_header = [
            Paragraph("<b>AI Tool / Technology</b>", self.styles["TableHeader"]),
            Paragraph("<b>Total Mentions</b>", self.styles["TableHeader"]),
            Paragraph("<b>Associated Guide IDs</b>", self.styles["TableHeader"]),
        ]
        tool_rows = [tool_header]

        for tool_name in sorted(tool_to_guides.keys()):
            guides = tool_to_guides[tool_name]
            tool_rows.append([
                Paragraph(f"<b>{tool_name}</b>", self.styles["TableCellBold"]),
                Paragraph(str(len(guides)), self.styles["TableCell"]),
                Paragraph(", ".join(guides), self.styles["TableCell"]),
            ])

        tool_table = Table(tool_rows, colWidths=[150, 70, 320])
        tool_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TEAL_PRIMARY),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(tool_table)
        story.append(Spacer(1, 20))

        # 3. Colophon / System Metadata
        story.append(Paragraph("Colophon &amp; Compilation Specifications", self.styles["SectionHeading"]))
        colophon_text = (
            "<b>Compilation Engine:</b> ReportLab PDF Generator v5.0.1 on Python 3.9<br/>"
            "<b>Document Geometry:</b> Standard Letter (8.5 x 11 in), 0.5 in margins, 540 pt printable width<br/>"
            "<b>Total Curated Guides:</b> 71 Resources across 5 Primary Categories<br/>"
            "<b>Repository Reference:</b> <code>ai-resource-library</code> &bull; Build Date: September 2026<br/>"
            "<b>Companion Deliverables:</b> <code>library.html</code> (Offline Search Portal) &bull; "
            "<code>MASTER_INDEX.md</code> &bull; <code>LEARNING_ROADMAP.md</code>"
        )
        story.append(Paragraph(colophon_text, self.styles["LegalNotice"]))

        return story

    def compile_pdf(self) -> Path:
        """Execute complete PDF compilation pipeline."""
        logger.info("Starting Master PDF compilation...")
        records = self.load_dataset()
        logger.info("Loaded %d records for PDF compilation.", len(records))

        # Assemble full document story
        story: List[Any] = []

        logger.info("Building Cover Page...")
        story.extend(self.build_cover_page())

        logger.info("Building Front Matter...")
        story.extend(self.build_front_matter())

        logger.info("Building Table of Contents...")
        story.extend(self.build_table_of_contents(records))

        logger.info("Building Learning Roadmaps...")
        story.extend(self.build_roadmaps_section())

        logger.info("Building Category Directories...")
        story.extend(self.build_category_directories(records))

        logger.info("Building Resource Profiles (71 uniform 2-page cards)...")
        story.extend(self.build_resource_profiles(records))

        logger.info("Building Master Indexes & Colophon...")
        story.extend(self.build_indexes_section(records))

        # Build document with custom canvas
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
            leftMargin=MARGIN_LEFT,
            rightMargin=MARGIN_RIGHT,
            topMargin=MARGIN_TOP,
            bottomMargin=MARGIN_BOTTOM,
            title="AI Resource Library — Master Reference Book",
            author="AI Resource Library Editorial",
            subject="100% Offline Personal Reference & Study under Fair Use",
        )

        logger.info("Compiling PDF flowables with MasterNumberedCanvas...")
        doc.build(story, canvasmaker=MasterNumberedCanvas)

        file_size = self.output_path.stat().st_size
        logger.info("Master PDF successfully written to %s (%d bytes)", self.output_path, file_size)
        return self.output_path


def main():
    """CLI runner for master reference PDF compilation."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    compiler = MasterPdfCompiler()
    pdf_file = compiler.compile_pdf()
    print(f"\n[Phase 7] Successfully compiled Master Reference PDF:\n  -> {pdf_file}")


if __name__ == "__main__":
    main()
