"""Prompt templates and schema validators for LLM analytical summarization."""

import re
from typing import Dict, Any, List

SYSTEM_PROMPT = """You are an elite AI curriculum architect and technical analyst building an offline personal reference library.
Your mission is to analyze the provided educational guide and author an ORIGINAL, HIGH-VALUE ANALYTICAL SUMMARY.

CRITICAL COPYRIGHT & FAIR-USE COMPLIANCE RULES:
1. STRICTLY PROHIBIT VERBATIM COPYING: Do NOT reproduce sentences or paragraphs word-for-word from the original text.
2. Re-frame all workflows, architectures, principles, and instructions in your own structured, analytical words.
3. Transform narrative stories or product sales copy into actionable engineering insights and clear takeaways.
4. Output must be in clean, professional GitHub-flavored Markdown adhering strictly to the mandatory 8-section schema.
5. Include concrete tools, commands, and actionable steps where applicable, without quoting copyrighted text.
"""

USER_PROMPT_TEMPLATE = """Analyze the following guide and produce an original, comprehensive analytical summary.

=== RESOURCE METADATA ===
ID: {id}
Title: {title}
Category: {category}
Subcategory: {subcategory}
Difficulty: {difficulty}
Source URL: {source_url}
Local Asset: {local_asset}
Status: {status}
Author: {author}
Detected Tools: {tools}

=== ARTICLE TABLE OF CONTENTS & HEADINGS ===
{headings}

=== EXTRACTED ARTICLE BODY TEXT ===
{body_text}

=== REQUIRED OUTPUT STRUCTURE ===
You MUST strictly follow this exact format with all 8 numbered markdown headers:

# {id} - {title}

- **Category:** {category} | **Subcategory:** {subcategory}
- **Difficulty:** {difficulty}
- **Source URL:** {source_url}
- **Local Asset:** {local_asset}
- **Status:** {status}

## 1. What This Resource Teaches
[2-3 detailed paragraphs synthesizing the core educational objectives, technical mechanics, and architectural foundation]

## 2. Why It Matters
[Substantive analysis of strategic value, efficiency gains, and relevance in modern AI workflows]

## 3. Target Audience
[Specific roles, experience levels, and ideal user profiles who gain maximum ROI from this resource]

## 4. Key Concepts & Principles
- **[Concept 1]**: [In-depth conceptual explanation]
- **[Concept 2]**: [In-depth conceptual explanation]
- **[Concept 3]**: [In-depth conceptual explanation]
- **[Concept 4]**: [In-depth conceptual explanation]

## 5. Tools & Technologies Mentioned
- **[Tool 1]**: [Role, functionality, and context within this workflow]
- **[Tool 2]**: [Role, functionality, and context within this workflow]

## 6. Practical Use Cases & Workflows
- **[Use Case / Workflow 1]**: [Synthesized step-by-step implementation walkthrough]
- **[Use Case / Workflow 2]**: [Synthesized step-by-step implementation walkthrough]

## 7. Prerequisites
- [Foundational concepts, software, environment configurations, or API access required]

## 8. Recommended Next Resources
- [Logical next topics, complementary skills, or subsequent modules in the curriculum]
"""

# Regex patterns for the 8 mandatory section headers
REQUIRED_SECTION_PATTERNS = [
    r"##\s*1\.\s*What\s+This\s+Resource\s+Teaches",
    r"##\s*2\.\s*Why\s+It\s+Matters",
    r"##\s*3\.\s*Target\s+Audience",
    r"##\s*4\.\s*Key\s+Concepts\s*(?:&|and)\s*Principles",
    r"##\s*5\.\s*Tools\s*(?:&|and)\s*Technologies\s*Mentioned",
    r"##\s*6\.\s*Practical\s+Use\s+Cases\s*(?:&|and)\s*Workflows",
    r"##\s*7\.\s*Prerequisites",
    r"##\s*8\.\s*Recommended\s+Next\s+Resources",
]


def build_user_prompt(record: Dict[str, Any], headings: List[str], body_text: str) -> str:
    """Construct the user prompt for a given guide record."""
    # Truncate body text to safe budget (~1500 words / ~2200 tokens) to respect 7000 ITPM / 8000 TPM
    words = body_text.split()
    if len(words) > 1500:
        truncated_body = " ".join(words[:1500]) + "\n\n[... content condensed for context budget ...]"
    else:
        truncated_body = body_text

    formatted_headings = "\n".join(f"- {h}" for h in headings) if headings else "N/A"
    formatted_tools = ", ".join(record.get("ai_tools", [])) or "None specified"
    local_asset = record.get("local_file") or "N/A (Web Only)"

    return USER_PROMPT_TEMPLATE.format(
        id=record["id"],
        title=record["title"],
        category=record["category"],
        subcategory=record.get("subcategory", "General"),
        difficulty=record["difficulty"],
        source_url=record["source_url"],
        local_asset=local_asset,
        status=record["status"],
        author=record.get("author", "Max Johnson"),
        tools=formatted_tools,
        headings=formatted_headings,
        body_text=truncated_body,
    )


def validate_summary_structure(markdown_text: str) -> bool:
    """Verify that all 8 mandatory section headers are present in the generated markdown."""
    for pattern in REQUIRED_SECTION_PATTERNS:
        if not re.search(pattern, markdown_text, re.IGNORECASE):
            return False
    return True


def get_missing_sections(markdown_text: str) -> List[str]:
    """Identify any missing mandatory section headers."""
    missing = []
    section_names = [
        "1. What This Resource Teaches",
        "2. Why It Matters",
        "3. Target Audience",
        "4. Key Concepts & Principles",
        "5. Tools & Technologies Mentioned",
        "6. Practical Use Cases & Workflows",
        "7. Prerequisites",
        "8. Recommended Next Resources",
    ]
    for pattern, name in zip(REQUIRED_SECTION_PATTERNS, section_names):
        if not re.search(pattern, markdown_text, re.IGNORECASE):
            missing.append(name)
    return missing
