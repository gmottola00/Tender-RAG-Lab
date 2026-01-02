"""Clean Neo4j database - remove all nodes and relationships."""

import asyncio
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


async def main():
    """Clean all data from Neo4j."""
    client = get_tender_graph_client()
    
    try:
        print("✅ Connected to Neo4j")
        
        # Delete all nodes and relationships
        query = "MATCH (n) DETACH DELETE n"
        await client.execute_write(query)
        
        # Get stats
        stats = await client.get_database_stats()
        print(f"\n📊 Database stats after cleanup:")
        for label, count in stats.items():
            print(f"   - {label}: {count}")
        
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
