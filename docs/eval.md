# Evaluation & Benchmarking Framework: AI Resource Library

> **Target Source:** [https://aiwithmax.com/](https://aiwithmax.com/)  
> **Source Documents:** [`docs/problemStatement.md`](file:///Users/mna/AI-Resource-Library/docs/problemStatement.md) | [`docs/architecture.md`](file:///Users/mna/AI-Resource-Library/docs/architecture.md) | [`docs/implementation-plan.md`](file:///Users/mna/AI-Resource-Library/docs/implementation-plan.md) | [`docs/edge-case.md`](file:///Users/mna/AI-Resource-Library/docs/edge-case.md)  
> **Version:** 1.0.0  
> **Status:** Comprehensive Evaluation Specification  

---

## Table of Contents

1. [Executive Summary & Evaluation Objectives](#1-executive-summary--evaluation-objectives)
2. [Evaluation Dimensions & Target Thresholds](#2-evaluation-dimensions--target-thresholds)
3. [Formal Metric Definitions & Scoring Formulations](#3-formal-metric-definitions--scoring-formulations)
4. [Dimension 1: Discovery & Ingestion Fidelity](#4-dimension-1-discovery--ingestion-fidelity)
5. [Dimension 2: Metadata Normalization & Catalog Integrity](#5-dimension-2-metadata-normalization--catalog-integrity)
6. [Dimension 3: LLM Analytical Summarization & Plagiarism Guard](#6-dimension-3-llm-analytical-summarization--plagiarism-guard)
7. [Dimension 4: Learning Roadmaps & Pedagogical Sequencing](#7-dimension-4-learning-roadmaps--pedagogical-sequencing)
8. [Dimension 5: Searchable Offline Web Portal Verification](#8-dimension-5-searchable-offline-web-portal-verification)
9. [Dimension 6: Master Reference PDF Publication Quality](#9-dimension-6-master-reference-pdf-publication-quality)
10. [Dimension 7: Legal, Ethical & Fair-Use Compliance](#10-dimension-7-legal-ethical--fair-use-compliance)
11. [Golden Benchmark Test Suite (Test Cases TC-01 to TC-25)](#11-golden-benchmark-test-suite-test-cases-tc-01-to-tc-25)
12. [LLM-as-a-Judge Evaluation Framework](#12-llm-as-a-judge-evaluation-framework)
13. [Production Readiness Scorecard & Release Gates](#13-production-readiness-scorecard--release-gates)

---

## 1. Executive Summary & Evaluation Objectives

The **Evaluation & Benchmarking Framework** defines the quantitative metrics, automated test suites, qualitative scoring rubrics, and acceptance gates required to validate the **Systematic Personal AI Resource Library**.

### Primary Evaluation Goals
- **Fidelity & Completeness:** Ensure 100% of publicly available resources from [aiwithmax.com](https://aiwithmax.com/) (target: $\ge 65$ guides) are discovered, cataloged, and classified without omission or duplication.
- **Copyright & Ethical Integrity:** Guarantee zero verbatim infringement; confirm that every summary is an original analytical distillation adhering to fair-use standards.
- **Structural Consistency:** Enforce 100% schema compliance across metadata (JSON/CSV), summary templates (8 mandatory sections), and roadmap DAGs.
- **Offline Self-Containment:** Prove that all end-user deliverables (`library.html`, `AI_RESOURCE_LIBRARY_MASTER.pdf`, `MASTER_INDEX.md`, `LEARNING_ROADMAP.md`) operate with zero internet access, zero external CDN dependencies, and zero broken links.

---

## 2. Evaluation Dimensions & Target Thresholds

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          7 CORE EVALUATION DIMENSIONS                            │
├─────────────────────────┬───────────────────────────────┬────────────────────────┤
│ 1. Ingestion Fidelity   │ 2. Catalog & Metadata         │ 3. LLM Summarization   │
│ • Discovery Recall 100% │ • Schema Valid 100%           │ • 8/8 Sections Present │
│ • Zero Crawl 429 Errors │ • Zero ID/URL Duplicates      │ • N-gram Overlap < 5%  │
├─────────────────────────┼───────────────────────────────┼────────────────────────┤
│ 4. Pedagogical Roadmaps │ 5. Offline Web Portal         │ 6. Master PDF Quality  │
│ • DAG Acyclicity 100%   │ • Air-Gap Network Calls = 0   │ • Zero Layout Overflow │
│ • 5-Stage Completeness  │ • Search Latency < 50ms       │ • ToC Bookmark Sync    │
├─────────────────────────┴───────────────────────────────┴────────────────────────┤
│ 7. Legal & Fair-Use Compliance: 100% Legal Non-Bypassing & Clear Attribution     │
└──────────────────────────────────────────────────────────────────────────────────┘
```

| Evaluation Dimension | Primary Focus | Key Metric | Target Pass Threshold |
|---|---|---|---|
| **1. Ingestion Fidelity** | Site scraping & extraction | Discovery Recall ($R_{\text{disc}}$) | **100%** ($\ge 65 / 65$ items) |
| **2. Catalog & Metadata** | Schemas, CSV, JSON, IDs | Field Completeness ($S_{\text{comp}}$) | **100%** (0 nulls in mandatory fields) |
| **3. LLM Summarizer** | Originality & 8-point schema | Structural Score & N-Gram Overlap | **$S_{\text{struct}} = 100\%$**, **$S_{\text{overlap}} < 5\%$** |
| **4. Pedagogical Roadmaps** | Paths A–H progression | DAG Validity & Milestone Count | **100% Acyclic**, **8 / 8 Paths Populated** |
| **5. Offline Web Portal** | `library.html` via `file://` | External Network Calls & Latency | **0 CDN Calls**, **Search Latency $< 50\text{ms}$** |
| **6. Master PDF Book** | Publication-grade PDF | Page Budgeting & ToC Accuracy | **0 Layout Errors**, **100% Bookmark Sync** |
| **7. Fair-Use & Legal** | Intellectual property boundaries | Protection Non-Bypass & Attribution | **0 Paywall Bypasses**, **100% Attributed** |

---

## 3. Formal Metric Definitions & Scoring Formulations

### 3.1 Discovery Recall ($R_{\text{disc}}$)
Measures the proportion of publicly accessible guides on the target website successfully discovered and archived.
$$R_{\text{disc}} = \frac{|\mathcal{D}_{\text{scraped}} \cap \mathcal{D}_{\text{target}}|}{|\mathcal{D}_{\text{target}}|} \times 100\%$$
- $\mathcal{D}_{\text{target}}$: Set of all guide slugs in the live site's catalog ($\ge 65$).
- $\mathcal{D}_{\text{scraped}}$: Set of guide slugs successfully extracted by the crawler.
- **Pass Criterion:** $R_{\text{disc}} = 100\%$.

### 3.2 Metadata Completeness Score ($S_{\text{comp}}$)
Evaluates whether all mandatory metadata fields are populated across all cataloged records.
$$S_{\text{comp}} = \frac{1}{N \cdot M} \sum_{i=1}^{N} \sum_{j=1}^{M} \mathbb{I}(f_{ij} \neq \emptyset \land \text{valid}(f_{ij})) \times 100\%$$
- $N$: Total number of resources ($N \ge 65$).
- $M$: Number of mandatory schema fields ($M = 12$: `id`, `slug`, `title`, `category`, `difficulty`, `description`, `source_url`, `content_type`, `author`, `status`, `topics`, `ai_tools`).
- $\mathbb{I}$: Indicator function returning 1 if valid, 0 otherwise.
- **Pass Criterion:** $S_{\text{comp}} = 100\%$.

### 3.3 Plagiarism & N-Gram Overlap Score ($S_{\text{plag}}$)
Quantifies consecutive word sequence similarity between raw scraped guide text ($T_{\text{source}}$) and the generated summary ($T_{\text{summary}}$) to prove fair-use original synthesis.
$$S_{\text{plag}} = \frac{|\text{N-grams}(T_{\text{summary}}, n) \cap \text{N-grams}(T_{\text{source}}, n)|}{|\text{N-grams}(T_{\text{summary}}, n)|} \times 100\% \quad (n = 6)$$
- Evaluates 6-gram word sequences (excluding common tool names and standard headings).
- **Pass Criterion:** $S_{\text{plag}} < 5.0\%$. Consecutive identical word runs must not exceed 15 words.

### 3.4 Summary Structural Compliance Score ($S_{\text{struct}}$)
Verifies that generated markdown summaries strictly satisfy all 8 required section headers.
$$S_{\text{struct}} = \frac{1}{8N} \sum_{i=1}^{N} \sum_{k=1}^{8} \mathbb{I}(\text{Header}_k \in \text{Summary}_i) \times 100\%$$
- **Pass Criterion:** $S_{\text{struct}} = 100\%$.

---

## 4. Dimension 1: Discovery & Ingestion Fidelity

### Automated Test Suite: `tests/test_crawler.py`
| Test ID | Test Description | Input / Condition | Expected Result | Pass Criteria |
|---|---|---|---|---|
| `TC-DISC-01` | Catalog Extraction | Homepage HTML with `guides = [...]` | Extract all 65 item dicts | List length $= 65$, all slugs unique |
| `TC-DISC-02` | Guide DOM Parser | `guide-claude-code-10x-setup-guide.html` | Extract title, TOC, author, body | Extracted clean text $> 1,000$ chars |
| `TC-DISC-03` | Rate Limiter Backoff | Simulated HTTP 429 response | Exponential backoff triggered | Sleep delay increases; retries $\le 5$ |
| `TC-DISC-04` | Clean Raw Cache | Scraping loop across all items | Write to `web-pages/AI-XXX.html` | 65 files exist; size $> 1\text{KB}$ each |
| `TC-DISC-05` | Unicode Handling | Guide title with `✦`, `“`, `”`, `—` | Text normalizer execution | Unicode normalized to clean UTF-8 |

---

## 5. Dimension 2: Metadata Normalization & Catalog Integrity

### Automated Test Suite: `tests/test_models.py`, `tests/test_inventory.py`
| Test ID | Test Description | Input / Condition | Expected Result | Pass Criteria |
|---|---|---|---|---|
| `TC-SCHEM-01` | Pydantic Instantiation | 65 raw extracted records | Validated `ResourceRecord` models | Zero `ValidationError` exceptions |
| `TC-SCHEM-02` | ID Sequence Consistency | Master record list | Deterministic ID sequence | `AI-001` through `AI-065`, zero gaps |
| `TC-SCHEM-03` | Taxonomy Normalization | Raw categories from source | Standard category taxonomy | Zero unknown unmapped categories |
| `TC-SCHEM-04` | CSV Delimiter Escaping | Description with commas and quotes | `inventory/master_inventory.csv` | Valid CSV; parses with standard parser |
| `TC-SCHEM-05` | CSV Formula Defense | Title beginning with `=CMD` | Leading single quote prepended | No spreadsheet execution vulnerability |
| `TC-SCHEM-06` | JSON Serialization | Full inventory export | `inventory/master_inventory.json` | Valid JSON; identical count on load |
| `TC-SCHEM-07` | Granular Metadata Sync | Per-resource metadata export | `metadata/AI-XXX.json` | 65 files match master JSON |

---

## 6. Dimension 3: LLM Analytical Summarization & Plagiarism Guard

### Automated Test Suite: `tests/test_summarizer.py`
| Test ID | Test Description | Input / Condition | Expected Result | Pass Criteria |
|---|---|---|---|---|
| `TC-SUMM-01` | 8-Point Header Presence | Generated summary files | Regex match for headers 1 through 8 | 100% of files match all 8 headers |
| `TC-SUMM-02` | Anti-Plagiarism Audit | Sliding 6-gram window check | Overlap against raw source page | $S_{\text{plag}} < 5\%$; no runs $>15$ words |
| `TC-SUMM-03` | Content Depth & Substance | Word count distribution | Comprehensive analysis | Word count between 350 and 900 words |
| `TC-SUMM-04` | Caching & Idempotence | Re-run summarizer on existing files | Local cache hit | Zero redundant LLM API calls |
| `TC-SUMM-05` | Hallucination Defense | Tools mentioned check | Cross-reference with raw guide | $\ge 90\%$ tools directly verified in text |

---

## 7. Dimension 4: Learning Roadmaps & Pedagogical Sequencing

### Automated Test Suite: `tests/test_generators.py`
| Test ID | Test Description | Input / Condition | Expected Result | Pass Criteria |
|---|---|---|---|---|
| `TC-ROAD-01` | Path Coverage | `LEARNING_ROADMAP.md` | Paths A through H present | All 8 paths documented |
| `TC-ROAD-02` | Milestone Completeness | Each of Paths A–H | 5 stages: Start $\rightarrow$ Next $\rightarrow$ Inter $\rightarrow$ Adv $\rightarrow$ Project | 5 stages per path with IDs assigned |
| `TC-ROAD-03` | DAG Acyclicity | Prerequisite dependency graph | Topological sort verification | Zero circular dependency cycles |
| `TC-ROAD-04` | Difficulty Ordering | Sequence of resources in path | Progression check | Difficulty monotonically non-decreasing |
| `TC-INDEX-01` | Master Index Completeness | `MASTER_INDEX.md` | Match against master inventory | 65 / 65 resources indexed under categories |

---

## 8. Dimension 5: Searchable Offline Web Portal Verification

### Verification Suite: Offline Air-Gap & Browser Smoke Tests
| Test ID | Test Description | Input / Condition | Expected Result | Pass Criteria |
|---|---|---|---|---|
| `TC-PORT-01` | Air-Gap Network Audit | Open `library.html` with network disabled | Zero failed external network requests | HTTP request count $= 0$ (no CDNs) |
| `TC-PORT-02` | Local File Protocol | Open via `file:///.../library.html` | UI renders cleanly; no CORS errors | Console error count $= 0$ |
| `TC-PORT-03` | Search Response Latency | Typing search query in search bar | Filtered card grid rendered | Render latency $< 50\text{ms}$ |
| `TC-PORT-04` | Multi-Faceted Filter | Select Category + Difficulty filter | Intersected card results | Filter count matches inventory exactly |
| `TC-PORT-05` | Summary Modal Preview | Click "Read Summary" on card | Modal opens with 8-point content | Content renders with formatted markdown |
| `TC-PORT-06` | XSS Attack Immunity | Malicious `<script>` in description | DOM text rendering | Injected script is escaped, not executed |

---

## 9. Dimension 6: Master Reference PDF Publication Quality

### Automated Test Suite: `tests/test_pdf_engine.py`
| Test ID | Test Description | Input / Condition | Expected Result | Pass Criteria |
|---|---|---|---|---|
| `TC-PDF-01` | PDF Header & Integrity | ReportLab build output | Valid binary `%PDF-` structure | File size $> 500\text{KB}$, zero exceptions |
| `TC-PDF-02` | Page Budget & Volume | Master PDF build | Complete coverage of 65 guides | Total page count $\ge 100$ pages |
| `TC-PDF-03` | Layout Overflow Audit | Long text descriptions in cards | `KeepTogether` block evaluation | Zero orphan headings; zero crashes |
| `TC-PDF-04` | Bookmark & ToC Sync | PDF outline tree extraction | ToC page number matches bookmark target | 100% bookmark-to-page alignment |
| `TC-PDF-05` | Unicode Font Rendering | Special characters (`✦`, `“`, `”`, `—`) | Canvas text rendering | Zero `UnicodeEncodeError`, zero black boxes |

---

## 10. Dimension 7: Legal, Ethical & Fair-Use Compliance

### Automated Audit Suite: `src/audit/qc_checker.py`
| Test ID | Test Description | Verification Method | Expected Result | Pass Criteria |
|---|---|---|---|---|
| `TC-LEGAL-01` | Paywall Non-Bypass | Inspect network crawler headers | Zero authentication tokens or bypass hacks | 100% public unauthenticated requests |
| `TC-LEGAL-02` | Asset Permitted Status | Verify downloaded files in `documents/` | All downloads originated from public links | Status correctly marked `DOWNLOADABLE` |
| `TC-LEGAL-03` | Restricted Classification | Assets requiring external platform | Check inventory status flag | Classified as `RESTRICTED` or `WEB_ONLY` |
| `TC-LEGAL-04` | Source Attribution | Audit `master_inventory.csv` & PDF cards | Canonical URL present on every entry | 100% of items have valid source URL |
| `TC-LEGAL-05` | Fair-Use Disclaimer | Inspect PDF book and summaries | Mandatory fair-use notice included | Notice present in front matter & cards |

---

## 11. Golden Benchmark Test Suite (Test Cases TC-01 to TC-25)

To ensure consistent end-to-end evaluation, the following **10 representative resources** serve as our **Golden Benchmark Callset**:

| Benchmark ID | Slug | Category | Difficulty | Characteristics / Stress Factor |
|---|---|---|---|---|
| **BM-01** | `the-ultimate-claude-starter-setup-guide` | Getting Started | Beginner | Standard baseline guide with structured sections |
| **BM-02** | `the-master-level-claude-guide` | Getting Started | Beginner to Advanced | Broad difficulty scope, long-form content |
| **BM-03** | `claude-code-10x-setup-guide` | Claude Code | Intermediate | Technical terminal instructions & CLI flags |
| **BM-04** | `ruflo-multi-agent-framework-setup-guide` | Claude Code | Advanced | Complex multi-agent workflow architecture |
| **BM-05** | `figma-claude-setup-guide` | Tools & Integrations | Intermediate | MCP connector setup with external API |
| **BM-06** | `remotion-claude-code-video-editor-setup-guide` | Tools & Integrations | Advanced | Code-heavy React components & programmatic video |
| **BM-07** | `the-competitor-intelligence-engine` | Building & Monetising | Advanced | End-to-end business system with n8n schema |
| **BM-08** | `33-best-claude-prompts-refreshed-for-sonnet-5` | Prompts & Skills | Beginner to Advanced | Prompt-heavy reference catalog |
| **BM-09** | `13-free-ai-courses-and-certifications` | Getting Started | Beginner | Link-heavy external certification index |
| **BM-10** | `how-to-scrape-thousands-of-leads-with-claude` | Tools & Integrations | Intermediate | Web scraping tutorial requiring anti-plagiarism care |

### Benchmark Pass/Fail Matrix
Every release build runs the full test suite against this Golden Callset. All 10 benchmark resources must score $\ge 95/100$ across all 7 dimensions.

---

## 12. LLM-as-a-Judge Evaluation Framework

To objectively score the qualitative rigor of generated summaries, an automated LLM Judge evaluates a random sample ($20\%$ of catalog) using a structured evaluation prompt.

### LLM Judge Rubric & Prompt Template

```markdown
SYSTEM:
You are an expert AI Curriculum Auditor evaluating the quality of an educational resource summary.
Score the provided summary across 4 criteria on a scale of 1 to 5 (5 = Excellent, 1 = Unacceptable).

CRITERIA:
1. ACCURACY & FIDELITY (1-5): Does the summary faithfully represent the source guide without factual hallucinations?
2. ACTIONABILITY & DEPTH (1-5): Are the workflows, use cases, and key concepts concrete and immediately useful?
3. STRUCTURAL RIGOR (1-5): Does the summary adhere strictly to the 8 required sections with clear formatting?
4. ORIGINAL SYNTHESIS (1-5): Is the content phrased in original analytical language rather than copied text?

OUTPUT FORMAT:
{
  "accuracy_score": <1-5>,
  "actionability_score": <1-5>,
  "structural_score": <1-5>,
  "originality_score": <1-5>,
  "composite_score": <float 1.0-5.0>,
  "findings": "<Detailed qualitative assessment>",
  "verdict": "<PASS|FAIL>"
}
```

### Passing Threshold
- **Composite Score:** Must be $\ge 4.2 / 5.0$.
- **Individual Scores:** No individual criterion may score $< 3.5$.

---

## 13. Production Readiness Scorecard & Release Gates

Before concluding the project and delivering the personal AI Resource Library, the automated evaluation pipeline (`python3 main.py --audit`) generates the final scorecard.

### Automated Release Gate Checklist

```markdown
## AI Resource Library Release Scorecard

[GATE 1: INGESTION & DISCOVERY]
- [x] Total guides discovered: >= 65 (Actual: 65)
- [x] Raw HTML cache files verified: 65 / 65
- [x] Crawler HTTP errors encountered: 0

[GATE 2: CATALOG & METADATA]
- [x] Master CSV inventory validity: 100% PASS
- [x] Master JSON inventory validity: 100% PASS
- [x] Granular per-resource metadata files: 65 / 65
- [x] Duplicate IDs or URLs detected: 0

[GATE 3: LLM SUMMARIES & COPYRIGHT]
- [x] Total summaries generated: 65 / 65
- [x] 8-point structural compliance: 100% PASS
- [x] N-gram plagiarism overlap: < 5.0% PASS
- [x] Verbatim runs > 15 words: 0

[GATE 4: COMPILATION & PRESENTATION]
- [x] MASTER_INDEX.md categorized resources: 65 / 65
- [x] LEARNING_ROADMAP.md paths populated: 8 / 8
- [x] library.html offline air-gap test: 0 external requests PASS
- [x] AI_RESOURCE_LIBRARY_MASTER.pdf compiled: >= 100 pages PASS
- [x] PDF ToC and bookmark synchronization: 100% PASS

[GATE 5: QUALITY AUDIT & REPORTING]
- [x] Broken internal relative links: 0
- [x] FINAL_REPORT.md compiled and published: PASS
```

### Execution Command for Complete Verification
```bash
# Execute full evaluation suite
pytest tests/ -v

# Run automated audit and generate FINAL_REPORT.md
python3 main.py --audit
```
