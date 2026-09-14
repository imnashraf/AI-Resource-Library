# Edge Cases & Failure Recovery Matrix: AI Resource Library

> **Target Source:** [https://aiwithmax.com/](https://aiwithmax.com/)  
> **Source Documents:** [`docs/problemStatement.md`](file:///Users/mna/AI-Resource-Library/docs/problemStatement.md) | [`docs/architecture.md`](file:///Users/mna/AI-Resource-Library/docs/architecture.md) | [`docs/implementation-plan.md`](file:///Users/mna/AI-Resource-Library/docs/implementation-plan.md)  
> **Version:** 1.0.0  
> **Status:** Comprehensive Corner Scenario & Edge Case Specification  

---

## Table of Contents

1. [Introduction & Edge Case Philosophy](#1-introduction--edge-case-philosophy)
2. [Domain 1: Ingestion, Network & Web Scraping Edge Cases](#2-domain-1-ingestion-network--web-scraping-edge-cases)
3. [Domain 2: Asset Acquisition & Download Security Edge Cases](#3-domain-2-asset-acquisition--download-security-edge-cases)
4. [Domain 3: Data Normalization & Inventory Edge Cases](#4-domain-3-data-normalization--inventory-edge-cases)
5. [Domain 4: LLM Analytical Summarizer & Plagiarism Guard Edge Cases](#5-domain-4-llm-analytical-summarizer--plagiarism-guard-edge-cases)
6. [Domain 5: Markdown Compilers & Roadmap Logic Edge Cases](#6-domain-5-markdown-compilers--roadmap-logic-edge-cases)
7. [Domain 6: Searchable Offline Web Portal (`library.html`) Edge Cases](#7-domain-6-searchable-offline-web-portal-libraryhtml-edge-cases)
8. [Domain 7: Master PDF Compilation (`AI_RESOURCE_LIBRARY_MASTER.pdf`) Edge Cases](#8-domain-7-master-pdf-compilation-ai_resource_library_masterpdf-edge-cases)
9. [Domain 8: Quality Control & Audit Engine Edge Cases](#9-domain-8-quality-control--audit-engine-edge-cases)
10. [Domain 9: Operating System, Filesystem & Cross-Platform Edge Cases](#10-domain-9-operating-system-filesystem--cross-platform-edge-cases)
11. [Master Corner Scenario Resolution Matrix](#11-master-corner-scenario-resolution-matrix)
12. [Human Escalation Scenarios & Decision Protocols](#12-human-escalation-scenarios--decision-protocols)

---

## 1. Introduction & Edge Case Philosophy

Building a resilient, production-grade offline knowledge library from dynamic web sources requires defending against failures across network, HTML parsing, legal constraints, data sanitization, LLM indeterminism, document formatting, and browser security models.

### Guiding Principles for Edge Case Handling
1. **Never Fail Silently:** Every anomaly must be caught, logged, categorized, and assigned a deterministic fallback status.
2. **Strict Legal Non-Bypassing:** If an asset requires authentication, paywall access, or violates copyright rules, **never attempt to bypass it**. Classify and catalog metadata transparently.
3. **Graceful Degradation:** A failure in an individual resource (e.g. an asset download or an LLM call) must never abort the entire batch pipeline.
4. **Idempotence & Atomic Writes:** Writing data to disk (CSV, JSON, Markdown, PDF) must be atomic or safely resumable to avoid corrupting master files.

---

## 2. Domain 1: Ingestion, Network & Web Scraping Edge Cases

### 1.1 HTTP 429 Too Many Requests & Rate Limiting
- **Symptom:** Target web server returns `HTTP 429` or begins dropping connection sockets.
- **Risk:** IP ban, incomplete scraping, corrupted page responses.
- **Handling Strategy:**
  1. Default request pacing: 1 request every 1.0s with $\pm 0.3\text{s}$ uniform jitter.
  2. If `429` is detected, read the `Retry-After` HTTP header if present.
  3. If no `Retry-After` header exists, initiate exponential backoff with jitter:
     $$\text{sleep} = 2^{\text{attempt}} + \text{uniform}(0.5, 1.5)\quad (\text{max 5 retries, cap at } 60\text{s})$$
  4. If retries exhaust, flag resource status as `ERROR: RATE_LIMITED`, log URL to `ai-resource-library/logs/crawler_errors.log`, and proceed to the next item.

### 1.2 Discrepancy Between Homepage Catalog and Individual Guide Pages
- **Symptom:** A guide slug is present in the homepage JavaScript `guides = [...]` array, but requesting `https://aiwithmax.com/guide-{id}.html` returns `HTTP 404` or redirects to the homepage.
- **Risk:** Null pointer exceptions, empty records in master inventory, broken links.
- **Handling Strategy:**
  1. Do not crash. Capture the HTTP status code.
  2. Mark status in inventory as `NOT_AVAILABLE`.
  3. Populate title, category, difficulty, and description from the homepage metadata.
  4. Set `notes: "Guide page returned HTTP 404 on target server"`.
  5. Exclude from LLM summarization pipeline until verified.

### 1.3 Malformed, Incomplete, or Mutating DOM Structures
- **Symptom:** Some guides use `<article>`, while others use `<div class="guide-content">`, `<main class="main">`, or nested containers.
- **Risk:** Empty text extracted, navigation/footer boilerplates captured as content.
- **Handling Strategy:**
  1. Multi-tier CSS selector fallback:
     ```python
     SELECTORS = [
         "article.guide-content",
         ".guide-body",
         "main .guide-wrap",
         ".page-wrap",
         "main"
     ]
     ```
  2. DOM sanitization: Strip non-content nodes before extracting text:
     - `header`, `footer`, `nav`, `.header`, `.toc-sidebar`, `.modal`, `script`, `style`, `svg`.
  3. Validation check: If extracted clean text is $< 150$ characters, raise `ScrapeContentWarning` and fallback to extracting paragraphs (`<p>`).

### 1.4 Non-Standard Characters, HTML Entities & UTF-8 Encoding Quirks
- **Symptom:** Titles or descriptions contain smart quotes (`“`, `”`), apostrophes (`’`), em-dashes (`—`), bullet stars (`✦`), non-breaking spaces (`&nbsp;`), or raw HTML entities (`&amp;`, `&quot;`).
- **Risk:** Corrupted CSV columns, broken markdown links, PDF font rendering squares (`[]`).
- **Handling Strategy:**
  1. Apply `html.unescape()` to all extracted text fields.
  2. Normalize unicode using `unicodedata.normalize("NFKC", text)`.
  3. Replace non-breaking spaces `\u00a0` with standard ASCII spaces `\u0020`.
  4. Strip zero-width spaces (`\u200b`, `\ufeff`).

### 1.5 Truncated or Zero-Byte HTTP Response Bodies
- **Symptom:** Server closes socket prematurely, returning a 200 OK header but an empty or partial HTML body.
- **Risk:** Corrupted cache files written to `web-pages/`.
- **Handling Strategy:**
  1. Enforce minimum content-length validation: if `len(response.content) < 500` bytes, discard payload.
  2. Mark attempt as failed and retry up to 3 times.
  3. Never overwrite an existing valid cached page with a zero-byte response.

---

## 3. Domain 2: Asset Acquisition & Download Security Edge Cases

### 2.1 Fake or Redirection Download Links
- **Symptom:** A link labeled "Download Cheat Sheet" redirects to an external service (Google Drive, Notion, Substack, Gumroad, Skool, YouTube, GitHub, or Typeform).
- **Risk:** Downloading multi-gigabyte files, landing on an OAuth page, or scraping third-party websites without permission.
- **Handling Strategy:**
  1. Check HTTP response headers with `HEAD` or stream inspection before writing:
     - Verify `Content-Type` starts with `application/pdf`, `application/zip`, `text/`, or `application/octet-stream`.
     - Reject `text/html` downloads that were expected to be binary documents.
  2. External Domain Whitelist / Verification:
     - If download link points outside `aiwithmax.com` (e.g. Skool/Gumroad paywall):
       - Do **not** attempt automated bypass.
       - Set `status = "RESTRICTED"` or `"WEB_ONLY"`.
       - Record `download_url = external_url` and `notes = "Requires external platform access"`.

### 2.2 Unsafe File Types & Executable Injection
- **Symptom:** An asset link points to an executable, archive script, or unsafe extension (`.exe`, `.sh`, `.bat`, `.scr`, `.vbs`, `.js`).
- **Risk:** Security compromise of the user's personal workstation.
- **Handling Strategy:**
  1. Strict extension whitelist for downloaded documents:
     ```python
     PERMITTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv", ".txt", ".md", ".zip"}
     ```
  2. Any file with an unapproved extension is rejected with status `ERROR: UNAPPROVED_FILE_TYPE`.

### 2.3 Unbounded File Size & DoS via Large Media
- **Symptom:** A resource links to a high-resolution video file (e.g. `.mp4`, `.mov`) or large dataset ($> 100\text{MB}$).
- **Risk:** Filling workstation disk, process freezing during network streaming.
- **Handling Strategy:**
  1. Inspect `Content-Length` header before initiating download stream.
  2. Enforce hard ceiling of **50 MB** per document asset.
  3. If `Content-Length > 50MB`, abort download, log warning, and record `notes: "Asset exceeds 50MB size limit (Web-only reference)"`.

### 2.4 Illegal Characters in OS Filenames
- **Symptom:** Guide title contains slashes, colons, pipes, or quotes (e.g. `Claude Code: 10x Setup Guide / Tips & Tricks`).
- **Risk:** Invalid filesystem path, directory traversal errors (`../../`), OS write failures.
- **Handling Strategy:**
  1. Use rigorous filename sanitization:
     ```python
     def sanitize_filename(name: str) -> str:
         # Remove illegal characters: / \ : * ? " < > |
         sanitized = re.sub(r'[\\/*?:"<>|]', '', name)
         # Collapse spaces and convert to snake/kebab
         sanitized = re.sub(r'\s+', '_', sanitized.strip())
         return sanitized[:80]  # Cap length to prevent path-length issues
     ```
  2. Standardize output: `documents/AI-XXX_{sanitized_title}.pdf`.

---

## 4. Domain 3: Data Normalization & Inventory Edge Cases

### 4.1 Duplicate Guides & Canonical Collision
- **Symptom:** A guide is linked twice under different categories or slightly altered slugs (e.g. `the-master-level-claude-guide` vs `master-level-claude-guide`).
- **Risk:** Duplicate inventory entries, fragmented IDs, inflated metrics.
- **Handling Strategy:**
  1. Primary Key: Normalized Canonical URL + Normalized Title Slug.
  2. Deduplication registry in memory during discovery:
     ```python
     seen_slugs: set[str] = set()
     seen_titles: set[str] = set()
     ```
  3. If duplicate title detected, merge categories if distinct, log duplicate removal, and maintain single canonical `AI-XXX` ID.

### 4.2 CSV Delimiter & Formula Injection (CSV Injection / DDE)
- **Symptom:** A title or description begins with `=`, `+`, `-`, `@`, or contains commas, semicolons, and double quotes.
- **Risk:**
  - Corrupted CSV parsing in Excel/Numbers.
  - Security risk: Execution of Dynamic Data Exchange (DDE) formulas in spreadsheet software.
- **Handling Strategy:**
  1. Sanitize leading formula triggers: If a field begins with `=`, `+`, `-`, or `@`, prefix with a single quote `'`.
  2. Use Python's native `csv.writer` with `quoting=csv.QUOTE_ALL` to ensure all fields containing commas, line breaks, or quotes are properly escaped.

### 4.3 Outlier & Non-Standard Categories
- **Symptom:** A guide belongs to an unexpected category not in the initial five (e.g., `AI Coding`, `Community`, `Uncategorized`, or empty category).
- **Risk:** Missing from `MASTER_INDEX.md`, breaking roadmap algorithms.
- **Handling Strategy:**
  1. Normalizer checks against canonical list.
  2. If unknown category is detected, do **not** discard. Place in dynamically generated `"Other Discovered Categories"` section.
  3. If category field is empty, assign `"General"`.

### 4.4 Multi-Level or Ambiguous Difficulty Ratings
- **Symptom:** Source specifies difficulty as `"Beginner to Advanced"`, `"All Levels"`, or leaves it blank.
- **Risk:** Pydantic enum validation failure.
- **Handling Strategy:**
  1. Pydantic enum schema explicitly supports:
     - `Beginner`
     - `Intermediate`
     - `Advanced`
     - `Beginner to Advanced`
  2. Fallback normalization: If blank or unrecognized, map to `Beginner to Advanced` as safest general classification.

---

## 5. Domain 4: LLM Analytical Summarizer & Plagiarism Guard Edge Cases

### 5.1 Plagiarism Guard: Verbatim Text Leakage
- **Symptom:** LLM regurgitates long consecutive sentences from the guide text instead of synthesizing original analysis.
- **Risk:** Copyright infringement, violation of fair use and project operating constraints.
- **Handling Strategy:**
  1. **Strict System Prompting:** Prohibit verbatim copying with penalty instructions.
  2. **Automated Plagiarism Check (N-gram overlap):**
     - Run a post-generation 4-gram sliding window comparison between raw page text and generated summary.
     - If consecutive identical word sequences $> 15$ words are detected (excluding tool names, commands, and headers), reject summary and re-prompt:
       > *"RE-PROMPT: The previous output contained verbatim excerpts from the source. Re-write section X entirely in your own analytical words without quoting source sentences."*
  3. Maximum 2 retries before flagging for human review.

### 5.2 Schema Non-Compliance (Missing Mandatory Sections)
- **Symptom:** LLM generates a well-written summary but omits one of the 8 mandatory section headers (e.g. forgets `## 7. Prerequisites`).
- **Risk:** Inconsistent UI rendering in `library.html`, broken parsing in PDF engine.
- **Handling Strategy:**
  1. Regex Header Verification:
     ```python
     MANDATORY_SECTIONS = [
         r"## 1\.\s+What This Resource Teaches",
         r"## 2\.\s+Why It Matters",
         r"## 3\.\s+Target Audience",
         r"## 4\.\s+Key Concepts & Principles",
         r"## 5\.\s+Tools & Technologies Mentioned",
         r"## 6\.\s+Practical Use Cases & Workflows",
         r"## 7\.\s+Prerequisites",
         r"## 8\.\s+Recommended Next Resources",
     ]
     ```
  2. If any pattern fails to match, trigger an automatic correction prompt requesting only the missing section or re-synthesizing with strict formatting.

### 5.3 Token Quota Depletion & Provider Outage
- **Symptom:** Provider returns `HTTP 429: Rate limit reached for tokens per minute (TPM)` or `HTTP 500: Internal Server Error`.
- **Risk:** Pipeline stops mid-batch; incomplete library.
- **Handling Strategy:**
  1. **Multi-Tier Fallback Cascade:**
     $$\text{Primary: Groq (gpt-oss-120b)} \longrightarrow \text{Secondary: Claude 3.5} \longrightarrow \text{Tertiary: OpenAI} \longrightarrow \text{Fallback: Local Ollama}$$
  2. **Local File Caching:**
     - Before invoking LLM, check if `summaries/AI-XXX.md` exists and is non-empty. If valid, skip call.
     - Saves token costs and allows resuming interrupted runs instantaneously.

### 5.4 Extremely Long or Extremely Short Guide Bodies
- **Scenario A (Massive Text):** Guide contains extensive tutorial code logs exceeding LLM context window ($> 15,000$ words).
  - *Strategy:* Hierarchical summarization. Extract headings and introductory paragraphs per section first, truncate raw logs, and feed condensed representation.
- **Scenario B (Sparse Text):** Guide consists only of an embedded YouTube video and 2 lines of text.
  - *Strategy:* Do not invent false facts. Synthesize summary using available title, video description, tools mentioned, and explicitly state in notes: *"Content primarily delivered via embedded video; summary synthesized from public transcript and overview notes."*

---

## 6. Domain 5: Markdown Compilers & Roadmap Logic Edge Cases

### 6.1 Circular or Deadlocked Prerequisites in Roadmaps
- **Symptom:** Path states Resource A requires Resource B, but Resource B requires Resource A.
- **Risk:** Infinite loops in dependency solvers, confusing learning paths.
- **Handling Strategy:**
  1. Build learning paths as Directed Acyclic Graphs (DAGs).
  2. Run topological sort validation on roadmap sequences:
     ```python
     import networkx as nx
     # If nx.is_directed_acyclic_graph(G) is False, break cycle and flag warning
     ```
  3. Fallback: Enforce strict difficulty progression (`Beginner` $\rightarrow$ `Intermediate` $\rightarrow$ `Advanced`).

### 6.2 Broken Relative Markdown Links
- **Symptom:** `MASTER_INDEX.md` links to `[Summary](summaries/AI-042.md)`, but the file was named `AI-42.md` or does not exist.
- **Risk:** Frustrating user experience, broken links on GitHub or IDE previewers.
- **Handling Strategy:**
  1. Automated pre-flight link checker in `src/audit/qc_checker.py`.
  2. Resolve all relative paths against filesystem before writing final markdown.
  3. Zero padding enforcement: Always format ID with 3 digits: `AI-{idx:03d}` (`AI-001`, `AI-010`, `AI-100`).

### 6.3 Markdown Table Breaking from Unescaped Pipe (`|`) Characters
- **Symptom:** Resource descriptions contain vertical bars `|` (e.g. `Claude | ChatGPT | Gemini comparison`).
- **Risk:** Distorted table columns in `MASTER_INDEX.md` and `FINAL_REPORT.md`.
- **Handling Strategy:**
  1. In any markdown table cell generation, escape pipe characters:
     ```python
     safe_cell = raw_text.replace("|", "\\|").replace("\n", " ")
     ```

---

## 7. Domain 6: Searchable Offline Web Portal (`library.html`) Edge Cases

### 7.1 Air-Gapped Failure via External CDN Calls
- **Symptom:** Web portal looks great online, but when opened on an air-gapped plane or offline workstation, icons, fonts, and scripts fail to load, resulting in an unstyled broken page.
- **Risk:** Total violation of the "Offline Personal Reference Library" core requirement.
- **Handling Strategy:**
  1. **Strict Zero-CDN Rule:** Zero external `<script src="...">` or `<link rel="stylesheet">`.
  2. Embed all CSS directly in `<style>` blocks.
  3. Embed all icons as inline SVG elements.
  4. Use modern system font stacks:
     ```css
     font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
     ```
     (Optional `@font-face` base64 inlining for brand fonts).
  5. Inlined JSON data payload directly in a `<script>` tag.

### 7.2 Browser Security & CORS Restrictions on `file:///` Protocol
- **Symptom:** Browser blocks `fetch('./inventory/master_inventory.json')` due to `CORS` / `Cross-Origin-Request` security policies when double-clicking `library.html` locally.
- **Risk:** Library displays empty cards and fails to load offline.
- **Handling Strategy:**
  1. **Do not use dynamic `fetch()` calls.**
  2. Inject the complete inventory JSON directly into `library.html` during the compilation step:
     ```html
     <script id="inventory-data" type="application/json">
     [ ... embedded JSON data ... ]
     </script>
     ```
  3. Parse with `JSON.parse(document.getElementById('inventory-data').textContent)`. Works 100% reliably in Chrome, Safari, Firefox, and Edge on `file://`.

### 7.3 Cross-Site Scripting (XSS) via Untrusted Scraped HTML
- **Symptom:** Scraped article title or description contains malicious `<script>` tags or HTML event handlers (`<img src=x onerror=alert(1)>`).
- **Risk:** Malicious script execution in user's browser session.
- **Handling Strategy:**
  1. Always use `textContent` instead of `innerHTML` when rendering user-facing text strings in JavaScript.
  2. In the lightweight inlined markdown renderer, sanitize raw HTML tokens before converting markdown headers and bullets.

### 7.4 Search Performance Lag on Low-Spec Hardware
- **Symptom:** User types quickly in search bar; typing lags because search executes on every keystroke against 65+ full summaries.
- **Risk:** Freezing UI, poor user experience.
- **Handling Strategy:**
  1. Debounce search input by 150ms.
  2. Search only against indexed lightweight fields by default (Title, Description, Category, Tools, Topics, ID).
  3. Only search full summary body if explicitly toggled by user.

---

## 8. Domain 7: Master PDF Compilation (`AI_RESOURCE_LIBRARY_MASTER.pdf`) Edge Cases

### 8.1 ReportLab Layout Overflow & Orphan Headings
- **Symptom:** Variable description lengths cause a resource card heading to render at the very bottom of Page 10, while its content renders on Page 11.
- **Risk:** Unprofessional, visually broken publication document.
- **Handling Strategy:**
  1. Wrap each 2-page or 1-page resource profile card in a `KeepTogether([heading, metadata_table, content_flowables])` container.
  2. If card exceeds maximum page height, dynamically trim paragraph spacing or scale font size from 10pt to 9pt.
  3. Insert explicit `PageBreak()` between distinct resources.

### 8.2 Unicode Font Rendering Failures (Black Rectangles / `?`)
- **Symptom:** Default standard PDF fonts (`Helvetica`, `Times-Roman`) cannot render UTF-8 characters like emojis, smart quotes, mathematical arrows (`→`, `↓`), or symbols (`✦`).
- **Risk:** ReportLab crashes with `UnicodeEncodeError` or prints ugly black boxes.
- **Handling Strategy:**
  1. Register a TrueType/OpenType Unicode font (e.g. `DejaVuSans.ttf`, `Inter.ttf`, or system fallback):
     ```python
     from reportlab.pdfbase import pdfmetrics
     from reportlab.pdfbase.ttfonts import TTFont
     pdfmetrics.registerFont(TTFont('UnicodeSans', font_path))
     ```
  2. Fallback character cleaner: Replace unrenderable glyphs with clean ASCII equivalents (`→` $\rightarrow$ `->`, `✦` $\rightarrow$ `*`).

### 8.3 Bookmark & Table of Contents Desynchronization
- **Symptom:** Table of Contents lists "Resource AI-040" at Page 82, but after pagination adjustments, it actually appears on Page 84.
- **Risk:** Broken reference manual.
- **Handling Strategy:**
  1. Use ReportLab's two-pass canvas (`NumberedCanvas`) or built-in page notification handlers.
  2. Dynamically record target page numbers during flowable rendering.
  3. Ensure PDF document outline bookmarks (`canvas.bookmarkPage()`) link directly to internal named destinations.

---

## 9. Domain 8: Quality Control & Audit Engine Edge Cases

### 9.1 False Positive Broken URLs during HEAD Requests
- **Symptom:** QC audit script reports 20 broken source URLs because the target web server returns `HTTP 403 Forbidden` or `HTTP 405 Method Not Allowed` when receiving `HEAD` requests.
- **Risk:** False alarms in `FINAL_REPORT.md`.
- **Handling Strategy:**
  1. If a `HEAD` request fails or returns non-200, automatically fallback to a polite `GET` request with a small byte-range header (`Range: bytes=0-10`).
  2. Only classify as broken if both `HEAD` and `GET` return 404, 500, or timeout.

### 9.2 Transient Network Fluctuations During Audits
- **Symptom:** A temporary WiFi hiccup during the audit causes 3 random URLs to fail with socket timeout.
- **Handling Strategy:**
  1. Implement 3 retries with 2-second pauses before marking any external URL as broken.
  2. Classify status in report distinctly: `VERIFIED`, `WARNING_UNRESPONSIVE`, `CONFIRMED_BROKEN`.

### 9.3 Partial Writes & Corrupted Deliverables on Interruption
- **Symptom:** User cancels script (Ctrl+C) while `master_inventory.csv` or `AI_RESOURCE_LIBRARY_MASTER.pdf` is half-written.
- **Risk:** Corrupted, unreadable files left in deliverable folder.
- **Handling Strategy:**
  1. Always write to a temporary file first:
     `ai-resource-library/inventory/master_inventory.csv.tmp`
  2. Atomically rename/replace file upon successful completion:
     ```python
     os.replace(temp_path, final_path)
     ```

---

## 10. Domain 9: Operating System, Filesystem & Cross-Platform Edge Cases

### 10.1 Path Separator Discrepancies (macOS vs Windows vs Linux)
- **Symptom:** Code uses hardcoded forward slashes `/` or backslashes `\`, causing crashes on alternative operating systems.
- **Handling Strategy:**
  1. Strictly use Python's standard `pathlib.Path` for all path manipulations.
  2. In markdown relative links and HTML, always normalize paths to forward slashes `/`.

### 10.2 Filename Case Sensitivity Issues
- **Symptom:** macOS filesystem is case-insensitive (APFS default), while Linux CI/CD environments are case-sensitive.
- **Risk:** `AI-001_guide.pdf` works on macOS but fails on Linux if requested as `AI-001_Guide.pdf`.
- **Handling Strategy:**
  1. Enforce strict lowercase naming conventions for all internal slugs, summary filenames, and metadata keys.
  2. ID prefixes must strictly follow uppercase: `AI-XXX`.

---

## 11. Master Corner Scenario Resolution Matrix

| # | Edge Case / Scenario | Severity | Trigger Condition | Automated Mitigation / Resolution |
|---|---|---|---|---|
| **E-01** | **Site Rate Limit (429)** | High | Rapid consecutive requests | Exponential backoff with jitter; limit crawler to 1 req/sec. |
| **E-02** | **Guide Page 404** | Medium | Slug listed on homepage but page deleted | Tag as `NOT_AVAILABLE`; preserve homepage summary; skip LLM. |
| **E-03** | **Paywall / Auth Encountered** | Critical | Asset requires login/payment | **Do not bypass.** Mark `RESTRICTED`, log URL, inform user. |
| **E-04** | **Unsafe File Type (.exe)** | Critical | Download link points to executable | Whitelist rejection; flag as `ERROR: UNAPPROVED_FILE_TYPE`. |
| **E-05** | **Asset Exceeds 50MB** | Medium | Large media/video linked | Stream check; abort download; mark `WEB_ONLY`. |
| **E-06** | **CSV Formula Injection** | High | Title starts with `=`, `+`, `-`, `@` | Prepend `'`; enforce full quotation in `csv.writer`. |
| **E-07** | **LLM Verbatim Copying** | High | LLM repeats source text verbatim | N-gram detector ($>15$ words); automatic re-prompting. |
| **E-08** | **Missing 8-Point Headers** | High | LLM output misses section header | Regex validator; automatic single-section repair prompt. |
| **E-09** | **LLM Rate Limit / Exhaustion** | High | Token quota reached on primary model | Fallback cascade (Groq $\rightarrow$ Claude $\rightarrow$ OpenAI $\rightarrow$ Ollama). |
| **E-10** | **CORS Failure on `file://`** | Critical | Double-clicking `library.html` offline | Inlined JSON payload directly in `<script>`; no `fetch()`. |
| **E-11** | **PDF Layout Overflow** | Medium | Variable text card height in ReportLab | `KeepTogether` flowable blocks; dynamic point resizing. |
| **E-12** | **ReportLab Unicode Error** | High | Emojis or smart quotes in PDF | Register TrueType Unicode font; sanitize glyph fallbacks. |
| **E-13** | **Circular Roadmap Dependency**| Medium | Resource A requires B, B requires A | DAG cycle detection via topological sort; enforce difficulty order. |
| **E-14** | **Pipe Breaking Markdown Tables**| Low | Resource text contains `|` | Auto-escape `\|` and replace newlines with spaces. |
| **E-15** | **Process Interruption / Crash**| High | User presses Ctrl+C during file write | Atomic file write via `.tmp` and atomic `os.replace()`. |

---

## 12. Human Escalation Scenarios & Decision Protocols

In accordance with Step 10 of the problem statement:
> *"Automate everything that can safely be automated. If something requires my decision, stop and clearly tell me."*

Whenever an ambiguous edge case cannot be resolved deterministically without human judgement, execution for that resource pauses and displays this standardized 4-part decision card:

### Escalation Case 1: Ambiguous Commercial Redistribution or License
- **1. What was found:** Resource links to a downloadable guide hosted on an external commercial platform with ambiguous personal reference rights.
- **2. Why decision is required:** Operating constraints prohibit downloading restricted or copyrighted third-party material without clarity.
- **3. Options available:**
  - **Option A (Recommended):** Record full metadata, author attribution, and source URL in inventory as `WEB_ONLY` without downloading the binary asset.
  - **Option B:** User manually verifies license, downloads the file, and drops it into `ai-resource-library/documents/`.
  - **Option C:** Completely purge this resource from the library.
- **4. Recommendation:** Option A preserves complete reference context while guaranteeing 100% legal compliance.

---

### Escalation Case 2: Permanent Primary LLM Quota Exhaustion
- **1. What was found:** All configured cloud LLM API keys have exhausted daily token allocations, and 25 summaries remain unbuilt.
- **2. Why decision is required:** Continuing cloud calls will fail; running local Ollama requires local CPU/GPU resources and time.
- **3. Options available:**
  - **Option A (Recommended):** Provide a secondary API key in `.env` (e.g. Claude or OpenAI) and resume.
  - **Option B:** Switch to local Ollama (`ollama run llama3.2`) to finish remaining summaries offline.
  - **Option C:** Pause summarization phase and generate partial inventory/roadmaps for already completed summaries.
- **4. Recommendation:** Option A or Option B allows immediate zero-loss completion.
