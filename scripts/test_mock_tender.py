"""Quick test script for NER → Neo4j pipeline with mock tender data.

This script tests the complete pipeline without needing to upload a PDF:
1. Creates realistic mock tender chunks
2. Extracts entities with spaCy NER
3. Populates Neo4j graph with requirements, deadlines, organizations
4. Queries the graph to verify data

Run:
    python scripts/test_mock_tender.py

Then check Neo4j browser:
    http://localhost:7474
    MATCH (n) RETURN n LIMIT 25
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.domain.tender.schemas.chunking import TenderChunk
from src.domain.tender.services.entity_extraction import create_entity_extraction_service
from src.infra.graph import get_tender_graph_client


async def test_mock_tender():
    """Test complete NER → Graph pipeline with mock data."""
    print("=" * 80)
    print("Testing NER → Neo4j Pipeline with Mock Tender Data")
    print("=" * 80)

    # Initialize
    print("\n[1/5] Initializing Neo4j connection...")
    graph_client = get_tender_graph_client()

    try:
        # Verify connectivity
        is_connected = await graph_client.verify_connectivity()
        if not is_connected:
            print("❌ Failed to connect to Neo4j")
            print("   Make sure Neo4j is running:")
            print("   docker-compose up -d neo4j")
            return

        print("✅ Connected to Neo4j")

        # Create schema
        await graph_client.create_tender_schema()
        print("✅ Schema created")

        # Create tender
        print("\n[2/5] Creating mock tender...")
        tender_code = "TEST-MOCK-001"

        await graph_client.create_tender(
            code=tender_code,
            title="Gara per servizi IT e cybersecurity - Test con dati mock",
            cpv_code="72000000",
            base_amount=500000.0,
            buyer_name="Comune di Milano",
            publication_date="2026-01-01",
        )
        print(f"✅ Created tender: {tender_code}")

        # Create mock chunks with realistic tender content
        print("\n[3/5] Creating mock chunks with entities...")
        mock_chunks = [
            TenderChunk(
                id="chunk-req-001",
                title="Requisiti di partecipazione",
                heading_level=2,
                text="""
                Requisiti di partecipazione obbligatori:
                1. Possesso della certificazione ISO 9001:2015 in corso di validità
                2. Fatturato minimo annuo di € 500.000 negli ultimi tre esercizi finanziari
                3. Esecuzione di almeno 3 servizi analoghi negli ultimi 5 anni
                4. Iscrizione alla Camera di Commercio obbligatoria
                5. Possesso dei requisiti di cui all'art. 80 del D.Lgs 50/2016 pena esclusione
                """,
                page_numbers=[5],
                tender_id="test-mock",
            ),
            TenderChunk(
                id="chunk-req-002",
                title="Requisiti tecnici",
                heading_level=2,
                text="""
                Ulteriori requisiti tecnici:
                - Il concorrente deve dimostrare esperienza nel settore IT
                - È richiesta certificazione di sicurezza ISO 27001
                - Necessario possedere almeno 10 dipendenti qualificati
                La mancanza anche di uno solo dei requisiti obbligatori comporta l'esclusione dalla gara.
                """,
                page_numbers=[6],
                tender_id="test-mock",
            ),
            TenderChunk(
                id="chunk-deadline-001",
                title="Scadenze",
                heading_level=2,
                text="""
                Scadenze importanti:
                - Sopralluogo obbligatorio: 15 febbraio 2026 ore 10:00
                - Termine ultimo per richiesta di chiarimenti: entro il 20 febbraio 2026
                - Scadenza presentazione offerte: entro e non oltre il 28 febbraio 2026 ore 12:00
                - Apertura delle buste: 1 marzo 2026 ore 14:00 presso la sede della stazione appaltante
                """,
                page_numbers=[12],
                tender_id="test-mock",
            ),
            TenderChunk(
                id="chunk-orgs-001",
                title="Stazione appaltante",
                heading_level=1,
                text="""
                Il Comune di Milano, in qualità di stazione appaltante, indice la presente gara.
                L'Autorità Nazionale Anticorruzione (ANAC) è l'ente di vigilanza.
                Per informazioni contattare il RUP Dott. Mario Rossi presso l'Ufficio Gare.
                La Regione Lombardia ha autorizzato la spesa con delibera n. 123/2025.
                """,
                page_numbers=[1],
                tender_id="test-mock",
            ),
            TenderChunk(
                id="chunk-money-001",
                title="Importo a base d'asta",
                heading_level=2,
                text="""
                L'importo complessivo a base di gara è pari a € 500.000,00 (cinquecentomila euro).
                L'importo è suddiviso in:
                - Servizi di sviluppo software: € 300.000,00
                - Servizi di cybersecurity: € 150.000,00
                - Manutenzione e supporto: € 50.000,00
                """,
                page_numbers=[8],
                tender_id="test-mock",
            ),
        ]

        print(f"✅ Created {len(mock_chunks)} mock chunks")

        # Extract entities and populate graph
        print("\n[4/5] Extracting entities and populating Neo4j graph...")
        service = create_entity_extraction_service(neo4j_client=graph_client)

        result = await service.extract_and_populate(
            chunks=mock_chunks,
            tender_id="test-mock",
            tender_code=tender_code,
        )

        print(f"\n✅ Entities extracted: {result['entity_count']}")
        print(f"   Entity breakdown:")
        for entity_type, entities in result['entities_by_type'].items():
            print(f"   - {entity_type}: {len(entities)} → {entities[:3]}{'...' if len(entities) > 3 else ''}")

        graph_stats = result.get("graph_stats", {})
        print(f"\n✅ Graph populated:")
        print(f"   - Organizations created: {graph_stats.get('organizations_created', 0)}")
        print(f"   - Requirements created: {graph_stats.get('requirements_created', 0)}")
        print(f"   - Deadlines created: {graph_stats.get('deadlines_created', 0)}")
        print(f"   - Relationships created: {graph_stats.get('relationships_created', 0)}")

        # Query the graph to verify
        print("\n[5/5] Verifying data in Neo4j...")

        # Get requirements
        requirements = await graph_client.get_requirements_for_tender(
            tender_code=tender_code,
            mandatory_only=False,
        )

        print(f"\n✅ Found {len(requirements)} requirements:")
        for req in requirements[:5]:  # Show first 5
            mandatory_label = "🔴 MANDATORY" if req.get("mandatory") else "⚪ Optional"
            desc = req.get("description", "")[:80]
            print(f"   {mandatory_label} - {desc}...")

        # Get deadlines
        deadlines = await graph_client.get_deadlines_for_tender(tender_code=tender_code)

        print(f"\n✅ Found {len(deadlines)} deadlines:")
        for deadline in deadlines:
            print(f"   [{deadline.get('type', 'unknown')}] {deadline.get('date_text', 'N/A')}")

        # Database stats
        print("\n📊 Neo4j Database Stats:")
        stats = await graph_client.get_database_stats()
        for key, value in stats.items():
            if value > 0:
                print(f"   - {key}: {value}")

        # Success
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\n🎯 Next Steps:")
        print("1. Open Neo4j Browser: http://localhost:7474")
        print("   Login with credentials from .env")
        print("\n2. Run these Cypher queries:")
        print(f"   // View tender and all connected nodes")
        print(f"   MATCH (t:Tender {{code: '{tender_code}'}})")
        print(f"   OPTIONAL MATCH (t)-[r]->(n)")
        print(f"   RETURN t, r, n")
        print(f"\n   // View mandatory requirements only")
        print(f"   MATCH (t:Tender {{code: '{tender_code}'}})-[:HAS_REQUIREMENT]->(r:Requirement)")
        print(f"   WHERE r.mandatory = true")
        print(f"   RETURN r.description")
        print(f"\n   // View all deadlines")
        print(f"   MATCH (t:Tender {{code: '{tender_code}'}})-[:HAS_DEADLINE]->(d:Deadline)")
        print(f"   RETURN d.type, d.date_text")
        print(f"   ORDER BY d.date_text")
        print("\n3. Test API endpoints:")
        print(f"   GET  http://localhost:8000/graph/requirements/{tender_code}?mandatory_only=true")
        print(f"   GET  http://localhost:8000/graph/deadlines/{tender_code}")
        print("\n4. Try with a real tender PDF:")
        print(f"   POST http://localhost:8000/extract-entities-and-populate-graph")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n[Cleanup] Closing Neo4j connection...")
        await graph_client.close()
        print("✅ Connection closed")


async def cleanup_mock_data():
    """Clean up mock test data from Neo4j."""
    print("\n" + "=" * 80)
    print("Cleaning up mock test data...")
    print("=" * 80)

    graph_client = get_tender_graph_client()

    try:
        is_connected = await graph_client.verify_connectivity()
        if not is_connected:
            print("❌ Failed to connect to Neo4j")
            return

        # Delete test tender and all related nodes
        query = """
        MATCH (t:Tender {code: 'TEST-MOCK-001'})
        OPTIONAL MATCH (t)-[r1]->(related)
        OPTIONAL MATCH (related)-[r2]->(chunk:Chunk)
        DETACH DELETE t, related, chunk
        """

        result = await graph_client.execute_write(query)
        print(f"✅ Cleaned up mock test data")

        # Verify cleanup
        stats = await graph_client.get_database_stats()
        print(f"\n📊 Database stats after cleanup:")
        for key, value in stats.items():
            if value > 0:
                print(f"   - {key}: {value}")

    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

    finally:
        await graph_client.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test NER → Neo4j with mock tender")
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up mock test data instead of running test"
    )

    args = parser.parse_args()

    if args.cleanup:
        asyncio.run(cleanup_mock_data())
    else:
        asyncio.run(test_mock_tender())
