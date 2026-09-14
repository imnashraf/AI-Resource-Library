"""Unit tests for lightweight local server and API backend."""

import json
from http.server import HTTPServer
import threading
import time
import httpx
import pytest

from src.server import LibraryRequestHandler


@pytest.fixture(scope="module")
def local_server():
    """Start server in a background thread for testing."""
    host = "127.0.0.1"
    port = 8765
    server = HTTPServer((host, port), LibraryRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)
    yield f"http://{host}:{port}"
    server.shutdown()
    server.server_close()


def test_server_root_serves_portal(local_server):
    """Verify GET / serves library.html with 200 OK and text/html."""
    resp = httpx.get(f"{local_server}/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "AI Resource Library" in resp.text
    assert "library-data" in resp.text


def test_server_api_health(local_server):
    """Verify GET /api/health returns healthy JSON status."""
    resp = httpx.get(f"{local_server}/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["catalog_count"] >= 65


def test_server_api_resources(local_server):
    """Verify GET /api/resources returns catalog items and handles filtering."""
    resp = httpx.get(f"{local_server}/api/resources")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 65
    assert len(data["resources"]) >= 65

    # Test filtering by category
    resp_cat = httpx.get(f"{local_server}/api/resources?category=Claude+Code")
    assert resp_cat.status_code == 200
    data_cat = resp_cat.json()
    assert data_cat["total"] > 0
    assert all(r["category"] == "Claude Code" for r in data_cat["resources"])


def test_server_api_single_resource(local_server):
    """Verify GET /api/resources/AI-001 returns metadata and summary."""
    resp = httpx.get(f"{local_server}/api/resources/AI-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "AI-001"
    assert "metadata" in data
    assert "summary" in data
    assert len(data["summary"]) > 100


def test_server_api_roadmaps(local_server):
    """Verify GET /api/roadmaps returns tracks and milestones."""
    resp = httpx.get(f"{local_server}/api/roadmaps")
    assert resp.status_code == 200
    data = resp.json()
    assert "tracks" in data
    assert len(data["tracks"]) == 8


def test_server_pdf_shortcut(local_server):
    """Verify GET /pdf serves the master PDF deliverable."""
    resp = httpx.get(f"{local_server}/pdf")
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers.get("content-type", "")
    assert resp.content.startswith(b"%PDF-")
