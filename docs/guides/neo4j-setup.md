# Neo4j Setup Guide

This guide covers the complete setup and configuration of Neo4j for Tender-RAG-Lab, including local development with Docker and production deployment with Neo4j Aura Cloud.

## Overview

Neo4j is used for storing structured tender knowledge: entities (Tender, Lot, Requirement, Deadline) and their relationships. It enables graph-based queries and reasoning alongside vector search.

## Quick Start

### 1. Start Neo4j

```bash
docker-compose up -d neo4j
```

Wait ~30 seconds for initialization.

### 2. Run Setup Script

```bash
PYTHONPATH=. uv run python scripts/setup_neo4j.py
```

This will:
- ✅ Test connection
- ✅ Create constraints (uniqueness)
- ✅ Create indexes (performance)
- ✅ Run CRUD tests
- ✅ Show database stats

### 3. Access Neo4j Browser

Open http://localhost:7474

**Login:**
- Username: `neo4j`
- Password: `tendergraph2025`

## Schema

### Node Types

```cypher
(:Tender {code, title, publication_date, cpv_code, base_amount, buyer_name, buyer_cf})
(:Lot {id, name, cpv_code, base_amount, description})
(:Requirement {id, type, description, mandatory, penalty_if_missing})
(:Deadline {id, type, date, time, location, notes})
(:Penalty {id, description, amount, trigger_condition})
(:Criterion {id, type, weight, max_points, description})
(:DocumentSection {id, chunk_id, section_path, page_numbers})
(:Organization {cf, name, type})
(:CPV {code, description, level})
```

### Relationships

```cypher
(Tender)-[:HAS_LOT]->(Lot)
(Lot)-[:REQUIRES]->(Requirement)
(Tender)-[:HAS_DEADLINE]->(Deadline)
(Tender)-[:HAS_PENALTY]->(Penalty)
(Tender)-[:HAS_CRITERION]->(Criterion)
(Requirement|Deadline|Penalty)-[:MENTIONED_IN]->(DocumentSection)
(Tender)-[:ISSUED_BY]->(Organization)
(Tender|Lot)-[:CLASSIFIED_AS]->(CPV)
(Requirement)-[:RELATED_TO]->(Requirement)  // dependencies
```

## Example Queries

### Get all mandatory requirements for a tender

```cypher
MATCH (t:Tender {code: "TENDER-2025-001"})-[:HAS_LOT]->(l:Lot)
MATCH (l)-[:REQUIRES]->(r:Requirement {mandatory: true})
RETURN t.title, l.name, r.description
```

### Find tenders with specific CPV

```cypher
MATCH (t:Tender)-[:CLASSIFIED_AS]->(cpv:CPV)
WHERE cpv.code STARTS WITH "72"  // IT services
RETURN t.code, t.title, t.base_amount
ORDER BY t.publication_date DESC
LIMIT 10
```

### Get all deadlines for a tender

```cypher
MATCH (t:Tender {code: "TENDER-2025-001"})-[:HAS_DEADLINE]->(d:Deadline)
RETURN d.type, d.date, d.notes
ORDER BY d.date
```

### Find similar tenders (same buyer + CPV)

```cypher
MATCH (t1:Tender {code: "TENDER-2025-001"})
MATCH (t2:Tender)
WHERE t2 <> t1
  AND t2.buyer_name = t1.buyer_name
  AND t2.cpv_code = t1.cpv_code
RETURN t2.code, t2.title, t2.publication_date, t2.base_amount
ORDER BY t2.publication_date DESC
```

### Get requirement dependencies

```cypher
MATCH (r1:Requirement {id: "REQ-001"})-[:RELATED_TO*]->(r2:Requirement)
RETURN r1.description as prerequisite,
       r2.description as dependent_requirement
```

## Python Usage

### Basic Connection

```python
from src.infra.graph import get_neo4j_client

client = get_neo4j_client()

# Verify connection
await client.verify_connectivity()

# Execute query
results = await client.execute_query(
    "MATCH (t:Tender) RETURN t LIMIT 5"
)

# Close connection
await client.close()
```

### Context Manager

```python
from src.infra.graph import get_neo4j_client

async with get_neo4j_client() as client:
    results = await client.execute_query(
        "MATCH (t:Tender {code: $code}) RETURN t",
        parameters={"code": "TENDER-2025-001"}
    )
```

### Create Nodes

```python
# Create tender
await client.execute_write(
    """
    CREATE (t:Tender {
        code: $code,
        title: $title,
        cpv_code: $cpv,
        base_amount: $amount,
        buyer_name: $buyer,
        publication_date: date($date)
    })
    """,
    parameters={
        "code": "TENDER-2025-001",
        "title": "IT Infrastructure",
        "cpv": "72000000",
        "amount": 500000.0,
        "buyer": "Ministero dell'Interno",
        "date": "2025-01-15"
    }
)
```

### Create Relationships

```python
# Link tender to lot
await client.execute_write(
    """
    MATCH (t:Tender {code: $tender_code})
    CREATE (l:Lot {
        id: $lot_id,
        name: $lot_name,
        base_amount: $amount
    })
    CREATE (t)-[:HAS_LOT]->(l)
    """,
    parameters={
        "tender_code": "TENDER-2025-001",
        "lot_id": "LOT-01",
        "lot_name": "Cloud Services",
        "amount": 200000.0
    }
)
```

## Configuration

Edit `.env`:

```bash
# Neo4j Knowledge Graph
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tendergraph2025
NEO4J_DATABASE=neo4j
```

For production (Neo4j Aura):

```bash
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your-secure-password>
NEO4J_DATABASE=neo4j
```

## Maintenance

### Clear Database

```python
from src.infra.graph import get_neo4j_client

client = get_neo4j_client()
await client.clear_database(confirm=True)  # ⚠️ Deletes everything!
```

### Get Statistics

```python
stats = await client.get_database_stats()
# {'nodes_Tender': 10, 'nodes_Lot': 25, 'relationships_total': 35}
```

### Backup (Docker)

```bash
# Create backup
docker exec tender-neo4j neo4j-admin database dump neo4j --to-path=/data/backups

# Restore backup
docker exec tender-neo4j neo4j-admin database load neo4j --from-path=/data/backups
```

## Performance Tips

1. **Always use indexes** for frequently queried properties
2. **Use parameters** in queries (prevents injection, enables plan caching)
3. **Limit results** with `LIMIT` clause
4. **Profile queries** with `EXPLAIN` or `PROFILE`
5. **Batch writes** when inserting multiple nodes

## Troubleshooting

### Connection Failed

```bash
# Check if Neo4j is running
docker ps --filter "name=neo4j"

# Check logs
docker logs tender-neo4j

# Restart
docker-compose restart neo4j
```

### Authentication Failed

Verify password in `.env` matches `docker-compose.yml`:
- `.env`: `NEO4J_PASSWORD=tendergraph2025`
- `docker-compose.yml`: `NEO4J_AUTH=neo4j/tendergraph2025`

### Slow Queries

```cypher
# Profile query
PROFILE
MATCH (t:Tender)-[:HAS_LOT]->(l:Lot)
WHERE t.cpv_code = "72000000"
RETURN t, l

# Check for missing indexes
CALL db.indexes()
```

## Resources

- [Neo4j Documentation](https://neo4j.com/docs/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [Python Driver API](https://neo4j.com/docs/python-manual/current/)
- [APOC Procedures](https://neo4j.com/labs/apoc/)

## Next Steps

1. ✅ Neo4j is running
2. ✅ Schema created
3. 📋 Implement NER for entity extraction
4. 📋 Create graph builder pipeline
5. 📋 Integrate with RAG retrieval
