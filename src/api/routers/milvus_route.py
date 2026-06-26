from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.deps import get_milvus_explorer, get_milvus_service
from src.api.deps import get_indexer, get_embedding_client
from quaerium.infra.vectorstores.milvus.exceptions import CollectionError


class CreateCollectionRequest(BaseModel):
    name: str
    shards_num: int = 2
    schema_: list[dict] = Field(..., alias="schema")  # Use alias to avoid shadowing
    index_params: Optional[dict] = None

    class Config:
        populate_by_name = True  # Allow both "schema" and "schema_"


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
    """Preview collection data with all available fields."""
    import logging
    logger = logging.getLogger(__name__)
    
    service = get_milvus_service()
    try:
        logger.info(f"Querying collection {name} with limit {limit}")
        
        client = service.connection.client
        
        # First, get schema to see available fields
        schema_info = client.describe_collection(collection_name=name)
        logger.info(f"Schema fields: {schema_info}")
        
        # Extract field names (exclude vector fields for readability)
        field_names = [
            field['name'] for field in schema_info.get('fields', [])
            if field.get('type') not in ['FLOAT_VECTOR', 'BINARY_VECTOR']
        ]
        
        logger.info(f"Available scalar fields: {field_names}")
        
        # Use MilvusClient.query() with discovered fields
        results = client.query(
            collection_name=name,
            filter="",  # Empty filter = get all
            output_fields=field_names if field_names else ["*"],
            limit=limit
        )
        
        logger.info(f"Query successful, got {len(results)} results")
        return {"collection": name, "count": len(results), "rows": results}
        
    except Exception as exc:
        logger.error(f"Error querying collection {name}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to query collection: {str(exc)}") from exc


@router.post("/collections")
async def create_collection(request: CreateCollectionRequest) -> dict:
    service = get_milvus_service()
    try:
        # Converti lo schema da lista di dict al formato atteso
        schema_dict = {}
        for field in request.schema_:
            field_name = field.get("name")
            if field_name:
                field_data = {k: v for k, v in field.items() if k != "name"}
                schema_dict[field_name] = field_data
        
        service.ensure_collection(
            name=request.name, 
            schema=schema_dict,
            shards_num=request.shards_num,
            index_params=request.index_params
        )
        return {"message": f"Collection '{request.name}' created successfully."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to create collection: {exc}") from exc


@router.delete("/collections/{name}")
async def delete_collection(name: str) -> dict:
    service = get_milvus_service()
    try:
        service.drop_collection(name=name)
        return {"message": f"Collection '{name}' deleted successfully."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete collection: {exc}") from exc


@router.get("/chunks/vector-search")
async def preview_vector_search(query: str, top_k: int = 5) -> dict:
    """Vector search against the tender chunks collection (for UI preview)."""
    indexer = get_indexer()
    embed_client = get_embedding_client()
    query_vec = embed_client.embed(query)
    try:
        results = indexer.search(query_embedding=query_vec, top_k=top_k)
        # Serialize results to ensure JSON compatibility
        serialized_results = []
        for result in results:
            serialized = {}
            for key, value in result.items():
                # Convert non-serializable types
                if hasattr(value, '__dict__'):
                    serialized[key] = str(value)
                elif callable(value):
                    continue  # Skip methods
                else:
                    serialized[key] = value
            serialized_results.append(serialized)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc
    return {"query": query, "top_k": top_k, "results": serialized_results}


__all__ = ["router"]
