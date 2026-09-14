"""Master CLI Orchestrator for the AI Resource Library Pipeline.

Provides a unified command-line interface to execute the full end-to-end pipeline,
individual phase modules, or automated quality assurance audits:

    python3 main.py --all           # Run all phases sequentially
    python3 main.py --phase 2       # Ingestion & Asset Harvesting
    python3 main.py --phase 3       # Cataloging & Master Inventory
    python3 main.py --phase 4       # LLM Analytical Summarizer
    python3 main.py --phase 5       # Master Index & Roadmaps
    python3 main.py --phase 6       # Searchable Web Portal (library.html)
    python3 main.py --phase 7       # Master Reference PDF
    python3 main.py --phase 8       # Quality Audit & Final Report
    python3 main.py --audit         # Run QA audit and generate FINAL_REPORT.md
"""

import argparse
import logging
import sys
from pathlib import Path

from src.config import PIPELINE_LOG_PATH, ensure_directories


def setup_logging():
    """Configure dual console and file logging to ai-resource-library/logs/pipeline.log."""
    ensure_directories()
    PIPELINE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PIPELINE_LOG_PATH, mode="a", encoding="utf-8"),
    ]

    logging.basicConfig(level=logging.INFO, format=log_format, handlers=handlers)


def run_phase_2():
    """Phase 2: Ingestion & Asset Harvesting."""
    print("\n=======================================================")
    print(">>> EXECUTING PHASE 2: Discovery, Crawling & Ingestion")
    print("=======================================================")
    from src.ingestion.run_ingestion import run_ingestion
    run_ingestion()


def run_phase_3():
    """Phase 3: Cataloging & Master Inventory."""
    print("\n=======================================================")
    print(">>> EXECUTING PHASE 3: Normalization & Inventory Export")
    print("=======================================================")
    from src.catalog.inventory import InventoryManager
    manager = InventoryManager()
    records = manager.generate_all()
    print(f"[Phase 3] Generated {len(records)} normalized inventory records.")


def run_phase_4():
    """Phase 4: LLM Analytical Summarizer & Copyright Guard."""
    print("\n=======================================================")
    print(">>> EXECUTING PHASE 4: LLM Analytical Summarizer")
    print("=======================================================")
    from src.summarizer.run_summarizer import run_summarizer_pipeline
    run_summarizer_pipeline()


def run_phase_5():
    """Phase 5: Master Index & Learning Roadmaps Compilers."""
    print("\n=======================================================")
    print(">>> EXECUTING PHASE 5: Index & Roadmap Compilers")
    print("=======================================================")
    from src.generators.run_generators import run_generators_pipeline
    run_generators_pipeline()


def run_phase_6():
    """Phase 6: Searchable Offline Web Portal (library.html)."""
    print("\n=======================================================")
    print(">>> EXECUTING PHASE 6: Searchable Web Portal (library.html)")
    print("=======================================================")
    from src.generators.portal_builder import PortalBuilder
    builder = PortalBuilder()
    out = builder.write_portal()
    print(f"[Phase 6] Generated web portal at: {out}")


def run_phase_7():
    """Phase 7: Offline Master Reference PDF Compilation."""
    print("\n=======================================================")
    print(">>> EXECUTING PHASE 7: Master Reference PDF Compilation")
    print("=======================================================")
    from src.generators.pdf_engine import MasterPdfCompiler
    compiler = MasterPdfCompiler()
    pdf_out = compiler.compile_pdf()
    print(f"[Phase 7] Generated Master PDF at: {pdf_out}")


def run_phase_8():
    """Phase 8: Quality Assurance Audit & Final Report."""
    print("\n=======================================================")
    print(">>> EXECUTING PHASE 8: QA Audit & Final Report")
    print("=======================================================")
    from src.audit.reporter import FinalReportCompiler
    reporter = FinalReportCompiler()
    report_file = reporter.write_report()
    print(f"[Phase 8] Generated Final Quality Audit Report at: {report_file}")


def run_all_phases():
    """Run all phases sequentially from Phase 2 to Phase 8."""
    print("\n*******************************************************")
    print("*** STARTING FULL PIPELINE RUN (PHASES 2 THROUGH 8) ***")
    print("*******************************************************")
    run_phase_2()
    run_phase_3()
    run_phase_4()
    run_phase_5()
    run_phase_6()
    run_phase_7()
    run_phase_8()
    print("\n*******************************************************")
    print("*** ALL PIPELINE PHASES COMPLETED SUCCESSFULLY 100% ***")
    print("*******************************************************\n")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Systematic Personal AI Resource Library Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py --all           Run all phases (2 through 8)
  python3 main.py --phase 2       Run Ingestion & Asset Harvesting
  python3 main.py --phase 3       Run Cataloging & Master Inventory
  python3 main.py --phase 4       Run LLM Summaries
  python3 main.py --phase 5       Run Index & Roadmaps Compilers
  python3 main.py --phase 6       Run Web Portal (library.html)
  python3 main.py --phase 7       Run Master Reference PDF
  python3 main.py --phase 8       Run Quality Audit & Final Report
  python3 main.py --audit         Run QA Audit & generate FINAL_REPORT.md
  python3 main.py --serve         Run local frontend portal & backend API server
        """,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Run all phases sequentially (Phases 2-8)")
    group.add_argument("--phase", type=int, choices=[2, 3, 4, 5, 6, 7, 8], help="Run a specific phase number (2-8)")
    group.add_argument("--audit", action="store_true", help="Execute Quality Assurance audit and update FINAL_REPORT.md")
    group.add_argument("--serve", action="store_true", help="Start local frontend portal and REST API backend server")

    parser.add_argument("--port", type=int, default=8000, help="Port to bind server (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")

    return parser.parse_args()


def run_serve(port: int = 8000, host: str = "127.0.0.1"):
    """Launch local web portal and REST API server."""
    from src.server import run_server
    run_server(port=port, host=host)


def main():
    """Main CLI entrypoint."""
    setup_logging()
    args = parse_args()

    phase_handlers = {
        2: run_phase_2,
        3: run_phase_3,
        4: run_phase_4,
        5: run_phase_5,
        6: run_phase_6,
        7: run_phase_7,
        8: run_phase_8,
    }

    if args.all:
        run_all_phases()
    elif args.audit:
        run_phase_8()
    elif args.serve:
        run_serve(port=args.port, host=args.host)
    elif args.phase in phase_handlers:
        phase_handlers[args.phase]()
    else:
        print(f"Unknown command or phase: {args.phase}")
        sys.exit(1)


if __name__ == "__main__":
    main()
