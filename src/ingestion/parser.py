"""Guide page HTML parser and content extractor.

Parses individual guide pages from aiwithmax.com, extracting clean text,
author, headings, table of contents, external tool links, and downloadable assets.
"""

import re
import html
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger("ingestion.parser")

# Known AI tools and platforms to detect in guide content
KNOWN_AI_TOOLS = [
    "Claude Code",
    "Claude 3.7 Sonnet",
    "Claude 3.5 Sonnet",
    "Claude Opus",
    "Claude Haiku",
    "Claude Projects",
    "Claude Desktop",
    "Claude Skills",
    "Claude Fable 5",
    "Claude",
    "ChatGPT",
    "OpenAI Codex",
    "GPT-4",
    "GPT-5",
    "Gemini CLI",
    "Gemini",
    "Ollama",
    "Cursor",
    "v0",
    "n8n",
    "Zapier",
    "Make.com",
    "Apify",
    "PostHog",
    "Remotion",
    "Figma",
    "Canva",
    "Wispr Flow",
    "Cookiy AI",
    "Ruflo",
    "Graphify",
    "NotebookLM",
    "ScrapeGraphAI",
    "Apollo",
    "Supabase",
    "Playwright",
    "Sentry",
    "Excel Copilot",
    "Groq",
]


class GuideParser:
    """Extracts structured content and metadata from guide HTML."""

    @staticmethod
    def parse_guide_html(
        raw_html: str,
        base_url: str = "https://aiwithmax.com/",
        fallback_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Parse raw guide HTML into a structured dictionary."""
        fallback = fallback_meta or {}
        soup = BeautifulSoup(raw_html, "html.parser")

        # 1. Title
        title_tag = soup.find("h1")
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else fallback.get("title", "Untitled Guide")

        # 2. Author
        author_tag = soup.find(class_=re.compile(r"author-name", re.I))
        author = author_tag.get_text(strip=True) if author_tag else fallback.get("author", "Max Johnson")

        # 3. Category & Difficulty
        cat_tag = soup.find(class_=re.compile(r"badge-cat", re.I))
        category = cat_tag.get_text(strip=True) if cat_tag else fallback.get("category", "General")

        diff_tag = soup.find(class_=re.compile(r"badge-diff", re.I))
        difficulty = diff_tag.get_text(strip=True) if diff_tag else fallback.get("difficulty", "Beginner")

        # 4. Table of Contents
        toc = []
        toc_box = soup.find(class_=re.compile(r"toc-box", re.I))
        if toc_box:
            for li in toc_box.find_all("li"):
                item_text = li.get_text(strip=True)
                if item_text:
                    toc.append(item_text)

        # 5. Article Body Text & Headings
        article_tag = soup.find("article", class_=re.compile(r"guide-content", re.I))
        if not article_tag:
            article_tag = soup.find("div", class_=re.compile(r"guide-content", re.I)) or soup.find("main")

        headings = []
        clean_text = ""
        outbound_links = []
        download_links = []

        if article_tag:
            for h in article_tag.find_all(["h2", "h3", "h4"]):
                h_text = h.get_text(strip=True)
                if h_text and h_text not in headings:
                    headings.append(h_text)

            clean_text = article_tag.get_text(separator="\n", strip=True)

            # Extract links
            for a in article_tag.find_all("a", href=True):
                href = a["href"].strip()
                full_url = urljoin(base_url, href)
                text = a.get_text(strip=True)

                # Check if download link
                lower_href = href.lower()
                is_download = (
                    any(ext in lower_href for ext in [".pdf", ".zip", ".docx", ".xlsx", ".csv"])
                    or "download" in lower_href
                    or "download" in text.lower()
                )

                link_info = {"text": text, "url": full_url}
                if is_download:
                    download_links.append(link_info)
                elif full_url.startswith("http") and "aiwithmax.com" not in full_url:
                    outbound_links.append(link_info)

        # 6. Detect AI Tools
        text_to_search = f"{title} {clean_text}"
        detected_tools = []
        for tool in KNOWN_AI_TOOLS:
            pattern = rf"\b{re.escape(tool)}\b"
            if re.search(pattern, text_to_search, re.IGNORECASE):
                if tool not in detected_tools:
                    detected_tools.append(tool)

        # 7. Derive Topics
        topics = [category]
        for heading in headings[:6]:
            # Add shortened topic keywords
            cleaned_heading = re.sub(r"^Chapter \d+:\s*", "", heading, flags=re.I).strip()
            if cleaned_heading and len(cleaned_heading) < 35:
                if cleaned_heading not in topics:
                    topics.append(cleaned_heading)

        return {
            "title": html.unescape(title),
            "author": html.unescape(author),
            "category": html.unescape(category),
            "difficulty": html.unescape(difficulty),
            "description": fallback.get("description", ""),
            "toc": toc,
            "headings": headings,
            "clean_text": clean_text,
            "word_count": len(clean_text.split()),
            "outbound_links": outbound_links,
            "download_links": download_links,
            "ai_tools": detected_tools,
            "topics": topics,
        }
