# Systematic Personal AI Resource Library

> An offline-first, structured personal reference ecosystem for modern AI workflows.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Status: Complete](https://img.shields.io/badge/pipeline-100%25%20Verified%20(PASS)-success.svg)]()
[![Deliverables: 71 Guides](https://img.shields.io/badge/cataloged-71%20Guides-purple.svg)]()
[![Master PDF: 166 Pages](https://img.shields.io/badge/master%20pdf-166%20pages-red.svg)]()
[![Air-Gapped Portal: Zero CDNs](https://img.shields.io/badge/portal-100%25%20Offline-orange.svg)]()
[![License: Personal Use](https://img.shields.io/badge/license-Personal%20Reference-lightgrey.svg)]()

---

## 1. Executive Overview

The **Systematic Personal AI Resource Library** is a robust, end-to-end data pipeline that harvests, normalizes, analyzes, indexes, and formats educational AI guides and workflows into a permanent, completely offline personal knowledge system.

### Key Deliverables Summary

| Deliverable | Location | Description / Key Attributes |
|---|---|---|
| **Offline Web Portal** | [`ai-resource-library/library.html`](ai-resource-library/library.html) | Standalone single-page app (661 KB), zero external CDN requests, inlined JSON dataset, live search, multi-filter drawer, and modal summary viewer. |
| **Master Reference Manual** | [`ai-resource-library/pdf/AI_RESOURCE_LIBRARY_MASTER.pdf`](ai-resource-library/pdf/AI_RESOURCE_LIBRARY_MASTER.pdf) | 166-page publication-grade PDF with cover page, dynamic ToC, 8 visual roadmap curricula, categorized directories, 2-page resource cards, and index. |
| **Categorized Master Index** | [`ai-resource-library/MASTER_INDEX.md`](ai-resource-library/MASTER_INDEX.md) | Markdown directory sorted alphabetically and taxonomically with verified cross-reference relative links. |
| **Curated Learning Roadmaps** | [`ai-resource-library/LEARNING_ROADMAP.md`](ai-resource-library/LEARNING_ROADMAP.md) | 8 role-specific tracks across 5 proficiency stages, featuring 40 milestone steps and technical rationales. |
| **Tabular Master Inventories** | [`ai-resource-library/inventory/master_inventory.csv`](ai-resource-library/inventory/master_inventory.csv)<br>[`ai-resource-library/inventory/master_inventory.json`](ai-resource-library/inventory/master_inventory.json) | 17-column CSV dataset with formula-safe RFC 4180 escaping and structured JSON dataset. |
| **Analytical Summaries** | [`ai-resource-library/summaries/`](ai-resource-library/summaries/) | 71 individual markdown files (`AI-001.md` through `AI-071.md`) conforming strictly to the 8-point analytical schema. |
| **Granular Metadata** | [`ai-resource-library/metadata/`](ai-resource-library/metadata/) | 71 individual JSON metadata files (`AI-001.json` through `AI-071.json`). |
| **Cached Web Pages** | [`ai-resource-library/web-pages/`](ai-resource-library/web-pages/) | 71 clean offline HTML guide pages stored locally. |
| **Quality Audit Report** | [`ai-resource-library/FINAL_REPORT.md`](ai-resource-library/FINAL_REPORT.md) | Automated QA report documenting gate checks, taxonomy metrics, tool frequencies, and verification telemetry. |

---

## 2. Master CLI Orchestrator (`main.py`)

The pipeline includes a unified CLI orchestrator that enables executing the full pipeline or individual modules.

```bash
# Activate virtual environment
source venv/bin/activate

# Execute the complete end-to-end pipeline sequentially (Phases 2 through 8)
python3 main.py --all

# Execute individual pipeline phases
python3 main.py --phase 2       # Phase 2: Ingestion & Asset Harvesting
python3 main.py --phase 3       # Phase 3: Cataloging & Master Inventory
python3 main.py --phase 4       # Phase 4: LLM Analytical Summaries
python3 main.py --phase 5       # Phase 5: Master Index & Learning Roadmaps
python3 main.py --phase 6       # Phase 6: Searchable Offline Web Portal (library.html)
python3 main.py --phase 7       # Phase 7: Master Reference PDF Manual
python3 main.py --phase 8       # Phase 8: Quality Control Audit & FINAL_REPORT.md

# Run automated Quality Assurance Audit and compile FINAL_REPORT.md
python3 main.py --audit
```

---

## 3. Offline Usage Guide

All generated artifacts are designed to function **100% offline** without active network access:

### 1. Interactive Search Portal (`library.html`)
Open [`ai-resource-library/library.html`](ai-resource-library/library.html) directly in any web browser:
```bash
# macOS
open ai-resource-library/library.html

# Linux
xdg-open ai-resource-library/library.html

# Windows
start ai-resource-library/library.html
```
- **Instant Search:** Fuzzy search across titles, descriptions, tools, and topics.
- **Dynamic Filters:** Filter by 5 canonical categories, 4 difficulty levels, and 12+ AI tools.
- **Card Modal:** Click any resource card to inspect its full 8-point summary in a modal overlay.
- **Air-Gapped Security:** Zero external web fonts, CDN scripts, or tracking beacons.

### 2. Master Reference Manual (`AI_RESOURCE_LIBRARY_MASTER.pdf`)
Open [`ai-resource-library/pdf/AI_RESOURCE_LIBRARY_MASTER.pdf`](ai-resource-library/pdf/AI_RESOURCE_LIBRARY_MASTER.pdf) in Preview, Adobe Acrobat, or any PDF reader:
- **Interactive PDF Bookmarks:** Jump directly to any Category, Roadmap Track, or Guide Card via the sidebar.
- **Structured 2-Page Cards:** Each guide features a standardized 2-page layout detailing Prerequisites, Executive Summary, Workflow Architecture, Implementation Steps, Limitations, and Learning Roadmap Placement.

### 3. Markdown Indexes in Code Editors
Browse [`ai-resource-library/MASTER_INDEX.md`](ai-resource-library/MASTER_INDEX.md) and [`ai-resource-library/LEARNING_ROADMAP.md`](ai-resource-library/LEARNING_ROADMAP.md) directly in VS Code or any markdown viewer. All relative links resolve to existing local summary and web-page files on disk.

---

## 4. Repository Structure

```
AI-Resource-Library/
├── docs/                                 # Centralized project specifications
│   ├── problemStatement.txt              # Original problem statement
│   ├── problemStatement.md               # Detailed markdown specification
│   ├── architecture.md                   # End-to-end pipeline architecture
│   ├── implementation-plan.md            # Phase-gated implementation roadmap
│   ├── edge-case.md                      # Edge case matrix & recovery protocols
│   └── eval.md                           # Evaluation rubric & gate criteria
├── config/
│   ├── settings.yaml                     # Crawl limits, timeouts, and paths
│   └── categories.yaml                   # Taxonomy & roadmap definitions
├── src/
│   ├── config.py                         # Path and settings manager
│   ├── ingestion/                        # Phase 2: Web crawler & HTML parser
│   ├── catalog/                          # Phase 3: Pydantic schemas & inventory generator
│   ├── summarizer/                       # Phase 4: Analytical summarizer & copyright guard
│   ├── generators/                       # Phase 5, 6, 7: Index, Roadmap, Portal & PDF engines
│   └── audit/                            # Phase 8: Quality control checker & reporter
├── ai-resource-library/                  # Final Deliverables Root (Offline-First)
│   ├── inventory/                        # master_inventory.csv & .json
│   ├── documents/                        # Download directory (verified fair use)
│   ├── web-pages/                        # 71 cached HTML guides
│   ├── summaries/                        # 71 analytical summaries (AI-001.md - AI-071.md)
│   ├── metadata/                         # 71 JSON metadata records
│   ├── pdf/                              # AI_RESOURCE_LIBRARY_MASTER.pdf (166 pages)
│   ├── logs/                             # pipeline.log execution history
│   ├── library.html                      # Standalone zero-CDN search portal
│   ├── MASTER_INDEX.md                   # Categorized markdown directory
│   ├── LEARNING_ROADMAP.md               # 8-track progressive curriculum
│   └── FINAL_REPORT.md                   # Quality audit & sign-off report
├── tests/                                # Comprehensive automated test suite (46 tests)
├── main.py                               # Master CLI orchestrator
├── requirements.txt                      # Python dependencies
└── README.md                             # Project documentation
```

---

## 5. Automated Quality Control Gates

Every deliverable is verified via automated checks in [`src/audit/qc_checker.py`](src/audit/qc_checker.py):

| Gate | Check | Criteria | Result |
|---|---|---|:---:|
| **Gate 1** | Deduplication | 0 duplicate IDs, slugs, or URLs across all 71 records | **PASS** |
| **Gate 2** | Schema Completeness | All 13 mandatory metadata attributes present and non-empty | **PASS** |
| **Gate 3** | File Asset Integrity | 213 local assets (HTML, summaries, JSON) verified on disk (>0 bytes) | **PASS** |
| **Gate 4** | Copyright & Summary Schema | 100% of summaries satisfy 8-point schema with 0 scraped HTML leaks | **PASS** |
| **Gate 5** | Relative Links | 364 markdown cross-reference links verified on disk with 0 broken | **PASS** |
| **Gate 6** | Offline Web Portal | 0 external scripts, 0 external CSS, inlined dataset, size >50 KB | **PASS** |
| **Gate 7** | Master Reference PDF | Valid PDF syntax, $\ge 100$ pages (166 achieved), outline bookmarks intact | **PASS** |
| **Gate 8** | Master Orchestration | `main.py` CLI runs all modules and generates `FINAL_REPORT.md` | **PASS** |

---

## 6. Running Automated Tests

Run the full pytest suite across all modules:

```bash
# Run all 46 automated unit and integration tests
PYTHONPATH=. venv/bin/pytest -v tests/
```

Test coverage includes:
- `tests/test_environment.py`: Directory structure and dependency imports.
- `tests/test_crawler.py` & `tests/test_parser.py`: HTML extraction and parsing.
- `tests/test_models.py` & `tests/test_inventory.py`: Schema validation and inventory export.
- `tests/test_summarizer.py` & `tests/test_summarizer_integration.py`: 8-point schema compliance.
- `tests/test_generators.py`: Master Index and Learning Roadmap link integrity.
- `tests/test_portal.py`: Zero-CDN air-gap verification and portal DOM checks.
- `tests/test_pdf_engine.py`: PDF page count, outline bookmarks, and XML sanitization.
- `tests/test_audit.py`: QualityControlChecker, FinalReportCompiler, and `main.py` CLI execution.

---

## 7. Legal & Fair Use Statement

This resource library is compiled strictly for personal, non-commercial educational and reference purposes under Fair Use principles:
1. **No Paywall Bypass:** Content requiring paid memberships or access tokens was strictly excluded.
2. **Transformative Synthesis:** All guide summaries are original analytical analyses conforming to an 8-point synthesis schema, rather than verbatim reproduction of external copyrighted copy.
3. **Personal Offline Use:** Strictly designed for personal private reference and local study.
