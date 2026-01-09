from neo4j import GraphDatabase
from app.config import settings
import re

class GraphService:
    def __init__(self):
        # Initialize the Neo4j Driver
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def sanitize(self, text: str) -> str:
        """
        Cleans text to be used as a Neo4j Relationship Type.
        Example: "worked at" -> "WORKED_AT"
        """
        if not text:
            return "RELATED_TO"
       
        clean = re.sub(r'[^a-zA-Z0-9]+', '_', text).upper()
        return clean.strip('_')

    def build_graph(self, data: dict):
        """
        Takes the JSON output from Phase 2 and writes it to Neo4j.
        """
        entities = data.get("entities", [])
        relationships = data.get("relationships", [])
        
        with self.driver.session() as session:
            # 1. Create Nodes (Entities)
            for entity in entities:
                session.run(
                    """
                    MERGE (n:Entity {id: $id})
                    SET n.type = $type, 
                        n.description = $description
                    """,
                    id=entity["id"],
                    type=entity["type"],
                    description=entity.get("description", "")
                )

            # 2. Create Relationships
            for rel in relationships:
                source_id = rel["source"]
                target_id = rel["target"]
                rel_type_str = self.sanitize(rel["type"]) 

                # We interpret the string safely here.
                query = f"""
                MATCH (s:Entity {{id: $source_id}})
                MATCH (t:Entity {{id: $target_id}})
                MERGE (s)-[r:{rel_type_str}]->(t)
                SET r.description = $description
                """
                
                try:
                    session.run(
                        query,
                        source_id=source_id,
                        target_id=target_id,
                        description=rel.get("description", "")
                    )
                except Exception as e:
                    print(f"Failed to create relationship {rel_type_str}: {e}")