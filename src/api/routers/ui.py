from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])


@router.get("/demo", response_class=HTMLResponse)
async def serve_demo() -> HTMLResponse:
    """Serve the demo HTML page."""
    html_path = Path("templates/demo.html")
    if not html_path.exists():
        return HTMLResponse(content="Demo template not found", status_code=404)
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@router.get("/tender-detail", response_class=HTMLResponse)
async def serve_tender_detail() -> HTMLResponse:
    """Serve the tender detail page."""
    html_path = Path("templates/tender_detail.html")
    if not html_path.exists():
        return HTMLResponse(content="Tender detail template not found", status_code=404)
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@router.get("/milvus", response_class=HTMLResponse)
async def serve_milvus() -> HTMLResponse:
    """Serve the Milvus explorer page."""
    html_path = Path("templates/milvus/index.html")
    if not html_path.exists():
        return HTMLResponse(content="Milvus template not found", status_code=404)
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


__all__ = ["router"]
