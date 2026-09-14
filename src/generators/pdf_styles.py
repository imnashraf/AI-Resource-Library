"""Styling Tokens, Typography, Flowables, and Canvas Architecture for Master PDF.

Provides custom ReportLab canvas with two-pass page numbering, running headers/footers,
clickable bookmarks, and publication-grade color and paragraph styles.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Flowable
from reportlab.pdfgen import canvas
from typing import Dict, Any

# Page Dimensions (Standard Letter with 0.5-inch margins)
PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN_LEFT = 36.0    # 0.5 in
MARGIN_RIGHT = 36.0   # 0.5 in
MARGIN_TOP = 48.0
MARGIN_BOTTOM = 46.0
PRINTABLE_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT  # 540 pt
PRINTABLE_HEIGHT = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

# Brand Color Palette
TEAL_PRIMARY = HexColor("#1A7A6A")
TEAL_DARK = HexColor("#0E473D")
TEAL_LIGHT = HexColor("#E8F5F3")
TEAL_BORDER = HexColor("#9FD5CE")

WARM_BG = HexColor("#F5F1EA")
CARD_BG = HexColor("#FAFAF8")
WHITE = HexColor("#FFFFFF")

TEXT_DARK = HexColor("#1A1D20")
TEXT_MUTED = HexColor("#555555")
TEXT_LIGHT = HexColor("#777777")
BORDER_COLOR = HexColor("#E2DDD5")
BORDER_SUBTLE = HexColor("#EAE5DC")

# Difficulty Colors
DIFF_COLORS = {
    "Beginner": {"text": HexColor("#065F46"), "bg": HexColor("#ECFDF5"), "border": HexColor("#A7F3D0")},
    "Intermediate": {"text": HexColor("#92400E"), "bg": HexColor("#FFFBEB"), "border": HexColor("#FDE68A")},
    "Advanced": {"text": HexColor("#5B21B6"), "bg": HexColor("#F5F3FF"), "border": HexColor("#DDD6FE")},
    "Beginner to Advanced": {"text": HexColor("#1E40AF"), "bg": HexColor("#EFF6FF"), "border": HexColor("#BFDBFE")},
}


class BookmarkFlowable(Flowable):
    """Inserts a PDF outline bookmark and sets page bookmark anchor."""

    def __init__(self, key: str, title: str, level: int = 0):
        super().__init__()
        self.key = key
        self.title = title
        self.level = level

    def wrap(self, availWidth, availHeight):
        return 0, 0

    def draw(self):
        self.canv.bookmarkPage(self.key)
        self.canv.addOutlineEntry(self.title, self.key, level=self.level, closed=False)


class SectionHeaderFlowable(Flowable):
    """Sets active section category for dynamic running headers on the canvas."""

    def __init__(self, section_name: str, key: str = "", level: int = 0):
        super().__init__()
        self.section_name = section_name
        self.key = key
        self.level = level

    def wrap(self, availWidth, availHeight):
        return 0, 0

    def draw(self):
        if hasattr(self.canv, "set_running_section"):
            self.canv.set_running_section(self.section_name)
        if self.key:
            self.canv.bookmarkPage(self.key)
            self.canv.addOutlineEntry(self.section_name, self.key, level=self.level, closed=False)


class MasterNumberedCanvas(canvas.Canvas):
    """Two-pass ReportLab canvas that generates dynamic headers and 'Page X of Y' footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self._running_section = "Executive Reference Manual"
        self._page_sections: Dict[int, str] = {}

    def set_running_section(self, section_name: str):
        self._running_section = section_name
        self._page_sections[self._pageNumber] = section_name

    def showPage(self):
        if self._pageNumber not in self._page_sections:
            self._page_sections[self._pageNumber] = self._running_section
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        # Suppress headers and footers on the cover page (Page 1)
        if self._pageNumber == 1:
            return

        self.saveState()

        # Running Header (Top)
        header_y = PAGE_HEIGHT - 28.0
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(TEAL_PRIMARY)
        self.drawString(MARGIN_LEFT, header_y, "AI RESOURCE LIBRARY")

        self.setFont("Helvetica", 7.5)
        self.setFillColor(TEXT_MUTED)
        active_sec = self._page_sections.get(self._pageNumber, "Master Reference Book")
        self.drawString(MARGIN_LEFT + 105, header_y, f"|   {active_sec}")

        self.setFont("Helvetica-Oblique", 7)
        self.setFillColor(TEXT_LIGHT)
        self.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, header_y, "100% Offline Personal Reference")

        # Decorative header rule
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.6)
        self.line(MARGIN_LEFT, header_y - 5, PAGE_WIDTH - MARGIN_RIGHT, header_y - 5)

        # Running Footer (Bottom)
        footer_y = 26.0
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.6)
        self.line(MARGIN_LEFT, footer_y + 12, PAGE_WIDTH - MARGIN_RIGHT, footer_y + 12)

        self.setFont("Helvetica", 7)
        self.setFillColor(TEXT_MUTED)
        self.drawString(
            MARGIN_LEFT,
            footer_y,
            "Personal AI Resource Library  •  Strictly for Private Educational Study & Reference (Fair Use)"
        )

        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(TEXT_DARK)
        self.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, footer_y, f"Page {self._pageNumber} of {total_pages}")

        self.restoreState()


def get_pdf_styles():
    """Create and return a comprehensive dictionary of publication-grade ParagraphStyles."""
    base = getSampleStyleSheet()

    styles = {
        # Cover Page Styles
        "CoverTitle": ParagraphStyle(
            "CoverTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=32,
            leading=38,
            textColor=WHITE,
            spaceAfter=10,
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=15,
            leading=20,
            textColor=TEAL_LIGHT,
            spaceAfter=25,
        ),
        "CoverMeta": ParagraphStyle(
            "CoverMeta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            textColor=WHITE,
        ),
        "CoverBadge": ParagraphStyle(
            "CoverBadge",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=TEAL_DARK,
        ),

        # Section & Major Headings
        "PartTitle": ParagraphStyle(
            "PartTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=TEAL_PRIMARY,
            spaceBefore=15,
            spaceAfter=10,
            keepWithNext=True,
        ),
        "SectionHeading": ParagraphStyle(
            "SectionHeading",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=TEAL_DARK,
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "SubSectionHeading": ParagraphStyle(
            "SubSectionHeading",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=TEXT_DARK,
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "CardSectionHeading": ParagraphStyle(
            "CardSectionHeading",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=13,
            textColor=TEAL_PRIMARY,
            spaceBefore=8,
            spaceAfter=3,
            keepWithNext=True,
        ),

        # Body Styles
        "Body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=TEXT_DARK,
            spaceAfter=5,
        ),
        "BodyLead": ParagraphStyle(
            "BodyLead",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=TEXT_DARK,
            spaceAfter=6,
        ),
        "BodyMuted": ParagraphStyle(
            "BodyMuted",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=TEXT_MUTED,
            spaceAfter=4,
        ),
        "BulletText": ParagraphStyle(
            "BulletText",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=11.5,
            textColor=TEXT_DARK,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=3,
        ),

        # Metadata & Card Styles
        "CardTitle": ParagraphStyle(
            "CardTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13.5,
            leading=17,
            textColor=TEXT_DARK,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "CardMeta": ParagraphStyle(
            "CardMeta",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=TEAL_PRIMARY,
            spaceAfter=4,
        ),
        "Callout": ParagraphStyle(
            "Callout",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8.2,
            leading=11.5,
            textColor=TEAL_DARK,
        ),
        "LegalNotice": ParagraphStyle(
            "LegalNotice",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.2,
            leading=9.5,
            textColor=TEXT_MUTED,
        ),

        # Table Cell Styles
        "TableHeader": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=WHITE,
            alignment=0,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10.5,
            textColor=TEXT_DARK,
            alignment=0,
        ),
        "TableCellBold": ParagraphStyle(
            "TableCellBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=10.5,
            textColor=TEXT_DARK,
            alignment=0,
        ),
        "ToCItem": ParagraphStyle(
            "ToCItem",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=13,
            textColor=TEXT_DARK,
            spaceAfter=4,
        ),
        "ToCSubItem": ParagraphStyle(
            "ToCSubItem",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=TEXT_MUTED,
            leftIndent=14,
            spaceAfter=2,
        ),
    }
    return styles
