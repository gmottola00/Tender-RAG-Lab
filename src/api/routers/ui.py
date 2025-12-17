from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["ui"])

# Configure templates
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def serve_home(request: Request) -> HTMLResponse:
    """Serve the home landing page."""
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/demo", response_class=HTMLResponse)
async def serve_demo(request: Request) -> HTMLResponse:
    """Serve the demo HTML page."""
    return templates.TemplateResponse("demo.html", {"request": request})


@router.get("/tender-detail", response_class=HTMLResponse)
async def serve_tender_detail(request: Request) -> HTMLResponse:
    """Serve the tender detail page."""
    return templates.TemplateResponse("tender_detail.html", {"request": request})


@router.get("/milvus", response_class=HTMLResponse)
async def serve_milvus(request: Request) -> HTMLResponse:
    """Serve the Milvus explorer page."""
    return templates.TemplateResponse("milvus/index.html", {"request": request})


@router.get("/milvus/databases", response_class=HTMLResponse)
async def serve_milvus_databases(request: Request) -> HTMLResponse:
    """Serve the Milvus databases management page."""
    return templates.TemplateResponse("milvus/databases.html", {"request": request})


@router.get("/milvus/collections", response_class=HTMLResponse)
async def serve_milvus_collections(request: Request) -> HTMLResponse:
    """Serve the Milvus collections management page."""
    return templates.TemplateResponse("milvus/collections.html", {"request": request})


@router.get("/milvus/collections/{collection_name}", response_class=HTMLResponse)
async def serve_collection_detail(request: Request, collection_name: str) -> HTMLResponse:
    """Serve the collection detail page."""
    return templates.TemplateResponse("milvus/collection_detail.html", {"request": request, "collection_name": collection_name})


__all__ = ["router"]
