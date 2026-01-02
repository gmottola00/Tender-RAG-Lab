"""
Example: How to integrate Knowledge Graph in RAG pipeline.

This demonstrates graph-enhanced retrieval and context assembly.
"""
import asyncio
from typing import List, Dict, Any

from src.infra.graph import get_tender_graph_client
from src.infra.graph.graph_indexer import (
    index_tender_to_graph,
    get_tender_context_for_chunks,
    find_related_tenders,
)


# =============================================================================
# EXAMPLE 1: Ingestion with Graph
# =============================================================================

async def example_ingestion():
    """
    How to index a tender document with graph enrichment.
    """
    print("📥 EXAMPLE 1: Ingestion with Graph\n")
    
    # Simulate tender metadata
    tender_metadata = {
        "title": "Fornitura servizi IT per digitalizzazione PA",
        "cpv_code": "72000000",  # IT services
        "base_amount": 500000.0,
        "buyer_name": "Ministero dell'Interno",
        "publication_date": "2025-01-15"
    }
    
    # Simulate chunks (in real flow, these come from document processing)
    chunks = [
        type('Chunk', (), {
            'id': 'chunk_001',
            'text': 'Il fornitore dovrà garantire servizi di cloud computing...',
            'metadata': {'page_number': 1, 'chunk_index': 0}
        })(),
        type('Chunk', (), {
            'id': 'chunk_002', 
            'text': 'Requisiti minimi: certificazione ISO 27001, esperienza 5 anni...',
            'metadata': {'page_number': 2, 'chunk_index': 1}
        })(),
    ]
    
    # Index to graph
    await index_tender_to_graph(
        tender_code="2025-001-IT",
        tender_metadata=tender_metadata,
        chunks=chunks
    )
    
    print("✅ Tender indexed to graph with 2 chunks\n")


# =============================================================================
# EXAMPLE 2: Graph-Enhanced Retrieval
# =============================================================================

async def example_retrieval():
    """
    How to enrich vector search results with graph context.
    """
    print("🔍 EXAMPLE 2: Graph-Enhanced Retrieval\n")
    
    # Simulate vector search results
    search_results = [
        {"chunk_id": "chunk_001", "score": 0.85, "text": "servizi di cloud computing..."},
        {"chunk_id": "chunk_002", "score": 0.78, "text": "certificazione ISO 27001..."},
    ]
    
    # Get graph context for chunks
    chunk_ids = [r["chunk_id"] for r in search_results]
    contexts = await get_tender_context_for_chunks(chunk_ids)
    
    # Enrich results
    for result in search_results:
        context = contexts.get(result["chunk_id"])
        if context:
            print(f"📄 Chunk: {result['text'][:50]}...")
            print(f"   From tender: {context['tender_title']}")
            print(f"   Buyer: {context['buyer_name']}")
            print(f"   Amount: €{context['base_amount']:,.0f}")
            print(f"   Score: {result['score']:.2f}\n")


# =============================================================================
# EXAMPLE 3: Find Related Tenders
# =============================================================================

async def example_related_tenders():
    """
    How to find tenders related by CPV or buyer.
    """
    print("🔗 EXAMPLE 3: Find Related Tenders\n")
    
    # Find tenders similar to "2025-001-IT"
    related = await find_related_tenders("2025-001-IT", limit=3)
    
    if related:
        print(f"Found {len(related)} related tenders:\n")
        for tender in related:
            print(f"  • {tender['title']}")
            print(f"    Buyer: {tender['buyer_name']}")
            print(f"    CPV: {tender['cpv_code']}")
            print(f"    Similarity: {tender['similarity_score']}\n")
    else:
        print("No related tenders found (database might be empty)")


# =============================================================================
# EXAMPLE 4: Context Assembly for LLM
# =============================================================================

async def example_context_assembly():
    """
    How to build enriched context for LLM generation.
    """
    print("🤖 EXAMPLE 4: Context Assembly for LLM\n")
    
    # Simulate search results
    chunk_ids = ["chunk_001", "chunk_002"]
    contexts = await get_tender_context_for_chunks(chunk_ids)
    
    # Build structured context
    llm_context = "Relevant tenders:\n\n"
    
    for chunk_id, context in contexts.items():
        llm_context += f"""
📋 Tender: {context['tender_title']}
🏢 Buyer: {context['buyer_name']}
💰 Amount: €{context['base_amount']:,.0f}
📅 Published: {context['publication_date']}
🏷️  CPV: {context['cpv_code']}

Relevant excerpt from chunk {chunk_id}:
[Chunk text would go here...]

---

"""
    
    print(llm_context)
    print("👆 This structured context goes to the LLM")


# =============================================================================
# EXAMPLE 5: Graph Statistics
# =============================================================================

async def example_graph_stats():
    """
    Get Knowledge Graph statistics.
    """
    print("📊 EXAMPLE 5: Graph Statistics\n")
    
    graph = get_tender_graph_client()
    
    try:
        stats = await graph.get_database_stats()
        
        print("Knowledge Graph contents:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Get tender-specific stats
        tender_stats = await graph.execute_query("""
            MATCH (t:Tender)
            OPTIONAL MATCH (t)-[:HAS_CHUNK]->(c:Chunk)
            RETURN t.code as tender_code,
                   t.title as title,
                   count(c) as chunk_count
            ORDER BY chunk_count DESC
            LIMIT 5
        """)
        
        if tender_stats:
            print("\nTop tenders by chunks:")
            for tender in tender_stats:
                print(f"  • {tender['tender_code']}: {tender['chunk_count']} chunks")
        
    finally:
        await graph.close()


# =============================================================================
# Run All Examples
# =============================================================================

async def main():
    """Run all examples."""
    print("=" * 70)
    print("Knowledge Graph Integration Examples")
    print("=" * 70 + "\n")
    
    try:
        await example_ingestion()
        await asyncio.sleep(0.5)
        
        await example_retrieval()
        await asyncio.sleep(0.5)
        
        await example_related_tenders()
        await asyncio.sleep(0.5)
        
        await example_context_assembly()
        await asyncio.sleep(0.5)
        
        await example_graph_stats()
        
        print("\n" + "=" * 70)
        print("✅ All examples completed!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
