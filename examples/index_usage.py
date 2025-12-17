"""Example usage of the refactored index system.

This module demonstrates how to use the new clean architecture
for vector indexing and search operations.
"""

from src.core.embedding.openai_embedding import OpenAIEmbedding
from src.infra.vectorstores.factory import (
    create_index_service,
    create_milvus_service,
    create_tender_stack,
)
from src.schemas.chunking import TokenChunk


def example_1_using_factory():
    """Example 1: Using create_tender_stack factory (recommended for tender app)."""
    # Create embedding client
    embed_client = OpenAIEmbedding(model="text-embedding-3-small")
    
    # Create complete stack with single factory call
    indexer, searcher = create_tender_stack(
        embed_client=embed_client,
        embedding_dim=1536,
        collection_name="my_tender_collection"
    )
    
    # Index some chunks
    chunks = [
        TokenChunk(
            id="chunk_1",
            text="Example tender document text",
            section_path="/section1",
            metadata={"type": "technical"},
            page_numbers=[1],
            source_chunk_id="src_1",
        )
    ]
    indexer.upsert_token_chunks(chunks)
    
    # Search
    results = searcher.hybrid_search("query text", top_k=5)
    print(f"Found {len(results)} results")


def example_2_generic_index_service():
    """Example 2: Using generic IndexService directly."""
    # Create embedding client
    embed_client = OpenAIEmbedding(model="text-embedding-3-small")
    
    # Create generic index service
    index_service = create_index_service(
        embedding_dim=1536,
        embed_fn=lambda texts: embed_client.embed_batch(texts),
        collection_name="generic_collection"
    )
    
    # Build schema (Milvus-specific for now)
    from pymilvus import DataType
    client = index_service.vector_store.connection.client
    schema = client.create_schema(auto_id=False)
    schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=64)
    schema.add_field("text", DataType.VARCHAR, max_length=65535)
    schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=1536)
    
    # Ensure collection
    index_service.ensure_collection(
        schema=schema,
        index_params={
            "field_name": "embedding",
            "index_type": "HNSW",
            "metric_type": "IP"
        }
    )
    
    # Upsert data
    data = [
        {"id": "1", "text": "Sample text", "embedding": [0.1] * 1536}
    ]
    index_service.upsert(data)
    
    # Search
    query_embedding = embed_client.embed("query")
    results = index_service.search(query_embedding, top_k=5)
    print(f"Found {len(results)} results")


def example_3_custom_search_strategies():
    """Example 3: Using custom search strategies."""
    from src.core.embedding.openai_embedding import OpenAIEmbedding
    from src.core.index.search_strategies import HybridSearch, KeywordSearch, VectorSearch
    from src.infra.vectorstores.factory import create_index_service
    
    # Create components
    embed_client = OpenAIEmbedding(model="text-embedding-3-small")
    index_service = create_index_service(
        embedding_dim=1536,
        embed_fn=lambda texts: embed_client.embed_batch(texts),
    )
    
    # Create search strategies
    vector_search = VectorSearch(
        index_service=index_service,
        embed_fn=lambda q: embed_client.embed(q)
    )
    
    keyword_search = KeywordSearch(index_service=index_service)
    
    hybrid_search = HybridSearch(
        vector_search=vector_search,
        keyword_search=keyword_search,
        alpha=0.7  # 70% vector, 30% keyword
    )
    
    # Execute searches
    vec_results = vector_search.search("semantic query", top_k=5)
    kw_results = keyword_search.search("exact keywords", top_k=5)
    hybrid_results = hybrid_search.search("mixed query", top_k=5)
    
    print(f"Vector: {len(vec_results)}, Keyword: {len(kw_results)}, Hybrid: {len(hybrid_results)}")


def example_4_milvus_service_directly():
    """Example 4: Using MilvusService directly for low-level operations."""
    from src.infra.vectorstores.factory import create_milvus_service
    
    # Create service
    service = create_milvus_service(
        uri="http://localhost:19530",
        db_name="default"
    )
    
    # List collections
    collections = service.explorer.list_collections()
    print(f"Collections: {collections}")
    
    # Query collection
    results = service.data.query(
        collection_name="tender_chunks",
        expr='text like "%contract%"',
        limit=10
    )
    print(f"Found {len(results)} matching documents")


if __name__ == "__main__":
    print("Index System Usage Examples")
    print("=" * 50)
    
    # Uncomment to run examples
    # example_1_using_factory()
    # example_2_generic_index_service()
    # example_3_custom_search_strategies()
    # example_4_milvus_service_directly()
