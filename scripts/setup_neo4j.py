"""
Neo4j setup and test script.

Run this to:
1. Verify Neo4j connection
2. Create schema constraints and indexes
3. Test basic CRUD operations
"""
import asyncio
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

from src.infra.graph import get_tender_graph_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_connection():
    """Test Neo4j connectivity."""
    logger.info("🔍 Testing Neo4j connection...")
    
    client = get_tender_graph_client()
    
    try:
        is_connected = await client.verify_connectivity()
        if is_connected:
            logger.info("✅ Neo4j connection successful!")
            return client
        else:
            logger.error("❌ Neo4j connection failed")
            return None
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
        return None


async def create_schema(client):
    """Create constraints and indexes."""
    logger.info("\n📐 Creating schema (constraints & indexes)...")
    
    try:
        await client.create_tender_schema()
        logger.info("✅ Schema created successfully")
    except Exception as e:
        logger.error(f"❌ Schema creation failed: {e}")
        raise


async def test_crud_operations(client):
    """Test basic CRUD operations."""
    logger.info("\n🧪 Testing CRUD operations...")
    
    # CREATE: Insert a test tender
    logger.info("Creating test tender...")
    result = await client.create_tender(
        code="TEST-2025-001",
        title="IT Infrastructure Services",
        cpv_code="72000000",
        base_amount=500000.0,
        buyer_name="Ministero dell'Interno",
        publication_date="2025-01-15"
    )
    logger.info(f"✅ Created: {result['nodes_created']} node(s)")
    
    # READ: Query the tender
    logger.info("Querying test tender...")
    tender = await client.get_tender_by_code("TEST-2025-001")
    
    if tender:
        logger.info(f"✅ Found: {tender['title']} (€{tender['base_amount']:,.0f})")
    else:
        logger.error("❌ Tender not found")
    
    # UPDATE: Add a lot
    logger.info("Adding lot to tender...")
    result = await client.add_lot_to_tender(
        tender_code="TEST-2025-001",
        lot_id="LOT-01",
        lot_name="Cloud Infrastructure",
        cpv_code="72212000",
        base_amount=200000.0
    )
    logger.info(f"✅ Added lot: {result['relationships_created']} relationship(s) created")
    
    # Complex query: Get tender with lots
    logger.info("Fetching tender with lots...")
    tender_with_lots = await client.get_tender_with_lots("TEST-2025-001")
    
    if tender_with_lots:
        logger.info(f"✅ Tender: {tender_with_lots['title']}")
        logger.info(f"   Lots: {tender_with_lots['lot_count']}, Total: €{tender_with_lots['total_lots_amount']:,.0f}")
    
    # DELETE: Clean up test data
    logger.info("Cleaning up test data...")
    delete_query = """
    MATCH (t:Tender {code: $code})
    DETACH DELETE t
    """
    
    result = await client.execute_write(
        delete_query,
        parameters={"code": "TEST-2025-001"}
    )
    logger.info(f"✅ Deleted: {result['nodes_deleted']} node(s)")


async def show_stats(client):
    """Show database statistics."""
    logger.info("\n📊 Database statistics:")
    
    try:
        stats = await client.get_database_stats()
        
        if not stats:
            logger.info("   (empty database)")
        else:
            for key, value in stats.items():
                logger.info(f"   {key}: {value}")
    except Exception as e:
        logger.warning(f"Could not fetch stats: {e}")


async def main():
    """Main setup and test workflow."""
    logger.info("=" * 60)
    logger.info("Neo4j Setup & Test Script")
    logger.info("=" * 60)
    
    # Test connection
    client = await test_connection()
    if not client:
        logger.error("\n❌ Cannot proceed without Neo4j connection")
        logger.info("\n💡 Make sure Neo4j is running:")
        logger.info("   docker-compose up -d neo4j")
        return
    
    try:
        # Create schema
        await create_schema(client)
        
        # Test CRUD
        await test_crud_operations(client)
        
        # Show stats
        await show_stats(client)
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ All tests passed! Neo4j is ready to use.")
        logger.info("=" * 60)
        logger.info("\n📚 Next steps:")
        logger.info("   1. Access Neo4j Browser: http://localhost:7474")
        logger.info("   2. Login: neo4j / tendergraph2025")
        logger.info("   3. Try: MATCH (n) RETURN n LIMIT 25")
        
    except Exception as e:
        logger.error(f"\n❌ Error during setup: {e}")
        raise
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
