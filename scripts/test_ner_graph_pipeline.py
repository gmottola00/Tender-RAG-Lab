"""Test complete NER → Neo4j → Hybrid Search pipeline.

This script tests the full integration:
1. Setup Neo4j schema
2. Create test tender
3. Extract entities from mock chunks
4. Populate graph with requirements, deadlines, organizations
5. Test graph-enriched search
6. Test graph-first queries (requirements, deadlines)

Run:
    python scripts/test_ner_graph_pipeline.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.domain.tender.services.entity_extraction import create_entity_extraction_service
from src.domain.tender.services.graph_retriever import create_graph_enriched_retriever
from src.domain.tender.schemas.chunking import TenderChunk
from src.infra.graph import get_tender_graph_client


async def test_pipeline():
    """Run complete test pipeline."""
    print("=" * 80)
    print("Testing NER → Neo4j → Hybrid Search Pipeline")
    print("=" * 80)

    # 1. Setup Neo4j
    print("\n[1/6] Setting up Neo4j schema...")
    graph_client = get_tender_graph_client()

    try:
        # Verify connectivity
        is_connected = await graph_client.verify_connectivity()
        if not is_connected:
            print("❌ Failed to connect to Neo4j")
            print("   Make sure Neo4j is running (docker-compose up -d neo4j)")
            return

        print("✅ Connected to Neo4j")

        # Create schema
        await graph_client.create_tender_schema()
        print("✅ Schema created (constraints + indexes)")

        # 2. Create test tender
        print("\n[2/6] Creating test tender...")
        tender_code = "TEST-2025-001"

        await graph_client.create_tender(
            code=tender_code,
            title="Gara test per servizi IT e sicurezza informatica",
            cpv_code="72000000",
            base_amount=500000.0,
            buyer_name="Comune di Milano",
            publication_date="2025-01-15",
        )
        print(f"✅ Created tender: {tender_code}")

        # 3. Create mock chunks with entities
        print("\n[3/6] Creating mock chunks with entities...")
        mock_chunks = [
            TenderChunk(
                id="chunk-001",
                title="Oggetto della gara",
                heading_level=1,
                text="""
                Il Comune di Milano indice la presente gara per la fornitura di servizi IT.
                È richiesta obbligatoriamente la certificazione ISO 27001 in corso di validità.
                La mancanza di tale certificazione comporta l'esclusione dalla gara.
                Scadenza per la presentazione delle offerte: entro il 31 marzo 2025.
                """,
                page_numbers=[1],
                tender_id="test-001",
                section_type="requirements",
            ),
            TenderChunk(
                id="chunk-002",
                title="Requisiti tecnici",
                heading_level=1,
                text="""
                Requisiti tecnici obbligatori:
                1. Esperienza minima di 5 anni nel settore IT (obbligatorio)
                2. Fatturato annuo superiore a €100.000 (requisito obbligatorio)
                3. Almeno 3 progetti simili realizzati negli ultimi 2 anni (necessario)

                Il sopralluogo obbligatorio si terrà il 15 febbraio 2025.
                Termine ultimo per i chiarimenti: 20 febbraio 2025.
                """,
                page_numbers=[2],
                tender_id="test-001",
                section_type="requirements",
            ),
            TenderChunk(
                id="chunk-003",
                title="Contatti e supervisione",
                heading_level=1,
                text="""
                Il RUP della gara è il Dott. Mario Rossi, contattabile presso l'Ufficio Appalti
                del Comune di Milano in Via Roma 10.

                La Regione Lombardia è ente supervisore per questa gara.
                """,
                page_numbers=[3],
                tender_id="test-001",
                section_type="administrative",
            ),
        ]

        print(f"✅ Created {len(mock_chunks)} mock chunks")

        # 4. Extract entities and populate graph
        print("\n[4/6] Extracting entities and populating graph...")
        service = create_entity_extraction_service(neo4j_client=graph_client)

        result = await service.extract_and_populate(
            chunks=mock_chunks,
            tender_id="test-001",
            tender_code=tender_code,
        )

        print(f"✅ Entities extracted: {result['entity_count']}")
        print(f"   - Organizations: {len(result['entities_by_type'].get('ORGANIZATION', []))}")
        print(f"   - People: {len(result['entities_by_type'].get('PERSON', []))}")
        print(f"   - Locations: {len(result['entities_by_type'].get('LOCATION', []))}")
        print(f"   - Dates: {len(result['entities_by_type'].get('DATE', []))}")
        print(f"   - Money: {len(result['entities_by_type'].get('MONEY', []))}")

        graph_stats = result.get("graph_stats", {})
        print(f"\n✅ Graph populated:")
        print(f"   - Organizations created: {graph_stats.get('organizations_created', 0)}")
        print(f"   - Requirements created: {graph_stats.get('requirements_created', 0)}")
        print(f"   - Deadlines created: {graph_stats.get('deadlines_created', 0)}")
        print(f"   - Relationships created: {graph_stats.get('relationships_created', 0)}")

        # 5. Test graph-first queries
        print("\n[5/6] Testing graph-first queries...")

        # Test requirements
        print("\n   a) Getting mandatory requirements...")
        retriever = create_graph_enriched_retriever(neo4j_client=graph_client)

        requirements = await retriever.search_requirements(
            tender_code=tender_code,
            mandatory_only=True,
        )

        print(f"   ✅ Found {len(requirements)} mandatory requirements:")
        for req in requirements[:3]:  # Show first 3
            print(f"      - [{req['requirement_id']}] {req['description'][:80]}...")

        # Test deadlines
        print("\n   b) Getting deadlines...")
        deadlines = await retriever.search_deadlines(tender_code=tender_code)

        print(f"   ✅ Found {len(deadlines)} deadlines:")
        for deadline in deadlines:
            print(f"      - [{deadline['type']}] {deadline['date_text']}")

        # 6. Test database stats
        print("\n[6/6] Database statistics...")
        stats = await graph_client.get_database_stats()
        print("   ✅ Neo4j database stats:")
        for key, value in stats.items():
            if value > 0:
                print(f"      - {key}: {value}")

        # Success summary
        print("\n" + "=" * 80)
        print("✅ PIPELINE TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Check Neo4j browser at http://localhost:7474")
        print("   Run query: MATCH (n) RETURN n LIMIT 25")
        print("2. Test API endpoints:")
        print(f"   POST /extract-entities-and-populate-graph")
        print(f"   GET /graph/requirements/{tender_code}")
        print(f"   GET /graph/deadlines/{tender_code}")
        print("3. Try hybrid search with real documents!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        print("\n[Cleanup] Closing connections...")
        await graph_client.close()
        print("✅ Connections closed")


async def cleanup_test_data():
    """Clean up test data from Neo4j."""
    print("\n" + "=" * 80)
    print("Cleaning up test data...")
    print("=" * 80)

    graph_client = get_tender_graph_client()

    try:
        is_connected = await graph_client.verify_connectivity()
        if not is_connected:
            print("❌ Failed to connect to Neo4j")
            return

        # Delete test tender and all related nodes
        query = """
        MATCH (t:Tender {code: 'TEST-2025-001'})
        OPTIONAL MATCH (t)-[r1]->(related)
        OPTIONAL MATCH (related)-[r2]->(chunk:Chunk)
        DETACH DELETE t, related, chunk
        """

        result = await graph_client.execute_write(query)
        print(f"✅ Cleaned up test data: {result}")

    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

    finally:
        await graph_client.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test NER → Graph pipeline")
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up test data instead of running test"
    )

    args = parser.parse_args()

    if args.cleanup:
        asyncio.run(cleanup_test_data())
    else:
        asyncio.run(test_pipeline())
