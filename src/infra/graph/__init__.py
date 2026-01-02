"""
Neo4j Knowledge Graph infrastructure for tender entities.
"""

# Generic client (reusable)
from src.infra.graph.base_client import Neo4jClient

# Tender-specific client (domain logic)
from src.infra.graph.tender_client import (
    TenderGraphClient,
    get_tender_graph_client,
)

# Backward compatibility (deprecated, use get_tender_graph_client)
def get_neo4j_client() -> TenderGraphClient:
    """
    Factory for Neo4j client.
    
    Deprecated: Use get_tender_graph_client() instead.
    """
    return get_tender_graph_client()


__all__ = [
    # Generic
    "Neo4jClient",
    # Tender-specific
    "TenderGraphClient",
    "get_tender_graph_client",
    # Backward compatibility
    "get_neo4j_client",
]
