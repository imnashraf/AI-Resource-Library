"""Lightweight Local Server & API Backend for the AI Resource Library.

Serves the interactive offline frontend portal (`library.html`) and provides
REST API endpoints for live querying of resources, summaries, roadmaps, and audit telemetry.
"""

import json
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import urllib.parse
from typing import Any, Dict, Optional

from src.config import (
    DELIVERABLES_ROOT,
    FINAL_REPORT_PATH,
    INVENTORY_DIR,
    MASTER_PDF_PATH,
    METADATA_DIR,
    PORTAL_HTML_PATH,
    PROJECT_ROOT,
    SUMMARIES_DIR,
)
from src.audit.qc_checker import QualityControlChecker
from src.generators.roadmap_generator import ROADMAP_TRACKS, TRACK_DURATIONS

logger = logging.getLogger("server")


class LibraryRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler serving the frontend portal and backend REST APIs."""

    def __init__(self, *args, directory=None, **kwargs):
        # Set base directory to deliverables root (ai-resource-library/)
        super().__init__(*args, directory=str(DELIVERABLES_ROOT), **kwargs)

    def do_GET(self):
        """Handle HTTP GET requests for static frontend files and API endpoints."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = urllib.parse.parse_qs(parsed.query)

        # 1. Root -> Serve Frontend Web Portal (library.html)
        if path == "" or path == "/index.html":
            self.serve_portal()
            return

        # 2. PDF Shortcut -> /pdf
        if path == "/pdf":
            self.serve_master_pdf()
            return

        # 3. Backend REST API Routing
        if path.startswith("/api/"):
            self.handle_api(path, query)
            return

        # 4. Fallback to standard static file serving from ai-resource-library/
        super().do_GET()

    def do_HEAD(self):
        """Handle HTTP HEAD requests."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "" or path == "/index.html":
            if not PORTAL_HTML_PATH.exists():
                self.send_error(404, "library.html not found.")
                return
            content = PORTAL_HTML_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            return
        if path == "/pdf":
            if not MASTER_PDF_PATH.exists():
                self.send_error(404, "Master PDF not found.")
                return
            content = MASTER_PDF_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Content-Disposition", 'inline; filename="AI_RESOURCE_LIBRARY_MASTER.pdf"')
            self.end_headers()
            return
        super().do_HEAD()

    def serve_portal(self):
        """Serve the standalone library.html portal."""
        if not PORTAL_HTML_PATH.exists():
            self.send_error(404, "library.html not found.")
            return
        content = PORTAL_HTML_PATH.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def serve_master_pdf(self):
        """Serve the master reference PDF manual."""
        if not MASTER_PDF_PATH.exists():
            self.send_error(404, "Master PDF not found.")
            return
        content = MASTER_PDF_PATH.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Content-Disposition", 'inline; filename="AI_RESOURCE_LIBRARY_MASTER.pdf"')
        self.end_headers()
        self.wfile.write(content)

    def handle_api(self, path: str, query: Dict[str, Any]):
        """Dispatch API requests."""
        # GET /api/health
        if path == "/api/health":
            self.send_json({
                "status": "healthy",
                "service": "AI-Resource-Library-Backend",
                "version": "1.0.0",
                "catalog_count": 71,
                "portal": "library.html",
                "pdf": "AI_RESOURCE_LIBRARY_MASTER.pdf",
            })
            return

        # GET /api/resources
        if path == "/api/resources":
            inv_file = INVENTORY_DIR / "master_inventory.json"
            if not inv_file.exists():
                self.send_json({"error": "master_inventory.json missing"}, status=500)
                return
            with open(inv_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Optional query filters
            category = query.get("category", [None])[0]
            difficulty = query.get("difficulty", [None])[0]
            search = query.get("q", [None])[0]

            filtered = data
            if category:
                filtered = [r for r in filtered if r.get("category", "").lower() == category.lower()]
            if difficulty:
                filtered = [r for r in filtered if r.get("difficulty", "").lower() == difficulty.lower()]
            if search:
                s = search.lower()
                filtered = [
                    r for r in filtered
                    if s in r.get("title", "").lower()
                    or s in r.get("description", "").lower()
                    or s in r.get("id", "").lower()
                ]

            self.send_json({
                "total": len(filtered),
                "resources": filtered,
            })
            return

        # GET /api/resources/<id>
        if path.startswith("/api/resources/"):
            res_id = path.split("/api/resources/")[-1].upper()
            meta_file = METADATA_DIR / f"{res_id}.json"
            sum_file = SUMMARIES_DIR / f"{res_id}.md"

            if not meta_file.exists():
                self.send_json({"error": f"Resource {res_id} not found"}, status=404)
                return

            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)

            summary_md = sum_file.read_text(encoding="utf-8") if sum_file.exists() else ""
            self.send_json({
                "id": res_id,
                "metadata": meta,
                "summary": summary_md,
            })
            return

        # GET /api/roadmaps
        if path == "/api/roadmaps":
            inv_file = INVENTORY_DIR / "master_inventory.json"
            records_map = {}
            if inv_file.exists():
                with open(inv_file, "r", encoding="utf-8") as f:
                    records_map = {r["id"]: r for r in json.load(f)}

            tracks = []
            for track_data in ROADMAP_TRACKS:
                track_id = track_data.get("path_id", "")
                milestones = []
                for m in track_data.get("stages", []):
                    rid = m.get("id")
                    rec = records_map.get(rid, {})
                    milestones.append({
                        "stage": m.get("stage"),
                        "id": rid,
                        "title": rec.get("title", m.get("title", "")),
                        "difficulty": rec.get("difficulty", ""),
                        "category": rec.get("category", ""),
                        "why_here": m.get("why_here", ""),
                    })
                tracks.append({
                    "id": track_id,
                    "title": track_data.get("title"),
                    "badge": track_data.get("badge"),
                    "duration": TRACK_DURATIONS.get(track_id, ""),
                    "description": track_data.get("description"),
                    "milestones": milestones,
                })
            self.send_json({"tracks": tracks})
            return

        # GET /api/audit
        if path == "/api/audit":
            checker = QualityControlChecker()
            audit_data = checker.run_full_audit(check_urls=False)
            self.send_json(audit_data)
            return

        # Unknown endpoint
        self.send_json({"error": f"Endpoint {path} not found"}, status=404)

    def send_json(self, data: Any, status: int = 200):
        """Helper to serialize and write JSON response."""
        content = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        """Route access logs through logger instead of stderr."""
        logger.info("%s - - [%s] %s", self.client_address[0], self.log_date_time_string(), format % args)


def run_server(port: int = 8000, host: str = "127.0.0.1"):
    """Start and run the HTTP server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, LibraryRequestHandler)
    print(f"\n=======================================================")
    print(f"🚀 AI Resource Library Server Running at:")
    print(f"   Frontend Portal : http://{host}:{port}/")
    print(f"   Master PDF      : http://{host}:{port}/pdf")
    print(f"   Backend Health  : http://{host}:{port}/api/health")
    print(f"   REST Resources  : http://{host}:{port}/api/resources")
    print(f"   REST Roadmaps   : http://{host}:{port}/api/roadmaps")
    print(f"   REST Audit      : http://{host}:{port}/api/audit")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        httpd.server_close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run AI Resource Library Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    run_server(port=args.port, host=args.host)
