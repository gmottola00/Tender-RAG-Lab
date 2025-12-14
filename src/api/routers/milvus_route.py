from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.providers import get_milvus_explorer
from src.api.providers import get_indexer, get_embedding_client
from src.core.index.vector.exceptions import CollectionError


router = APIRouter(prefix="/milvus", tags=["milvus"])


@router.get("/collections")
async def list_collections() -> list[dict]:
    explorer = get_milvus_explorer()
    return explorer.list_collections()


@router.get("/collections/{name}/schema")
async def collection_schema(name: str) -> dict:
    explorer = get_milvus_explorer()
    return explorer.collection_schema(name)


@router.get("/collections/{name}/data")
async def collection_data(
    name: str,
    limit: int = Query(100, ge=1, le=500),
    fields: str | None = Query(None, description="Comma-separated fields"),
) -> dict:
    explorer = get_milvus_explorer()
    output_fields = [f.strip() for f in fields.split(",")] if fields else None
    try:
        rows = explorer.get_collection_data(name, output_fields=output_fields, limit=limit)
        return {"collection": name, "count": len(rows), "rows": rows}
    except CollectionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/collections/{name}/preview")
async def collection_preview(
    name: str,
    limit: int = Query(20, ge=1, le=200),
) -> dict:
    explorer = get_milvus_explorer()
    try:
        rows = explorer.preview(name, limit=limit)
        return {"collection": name, "count": len(rows), "rows": rows}
    except CollectionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/chunks/vector-search")
async def preview_vector_search(query: str, top_k: int = 5) -> dict:
    """Vector search against the tender chunks collection (for UI preview)."""
    indexer = get_indexer()
    embed_client = get_embedding_client()
    query_vec = embed_client.embed(query)
    try:
        results = indexer.search(query_embedding=query_vec, top_k=top_k)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc
    return {"query": query, "top_k": top_k, "results": results}


__all__ = ["router"]
