from app.services.vector_service import VectorService
from app.services.llm_service import LLMService
from app.config import settings
from neo4j import GraphDatabase

class RAGService:
    def __init__(self):
        # Connect to existing services
        self.vector_service = VectorService()
        self.llm_service = LLMService()
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )

    def get_graph_context(self, question: str):
        """
        1. Identifies key entities in the user's question.
        2. Queries Neo4j to find related concepts.
        """
        # Step A: Ask LLM to extract entities from the question itself
      
        extraction = self.llm_service.extract_graph_data(question)
        
        # We only care about the entity IDs found in the question
        entities = [e["id"] for e in extraction.get("entities", [])]
        
        if not entities:
            return ""

        # Step B: Query Neo4j for neighbors of these entities
        context_lines = []
        with self.driver.session() as session:
            for entity in entities:
                # Find nodes connected to the entity mentioned in the question
                result = session.run(
                    """
                    MATCH (n:Entity {id: $id})-[r]-(connected)
                    RETURN n.id, type(r), connected.id, r.description
                    LIMIT 5
                    """,
                    id=entity
                )
                
                for record in result:
                   
                    line = f"{record['n.id']} {record['type(r)']} {record['connected.id']} ({record['r.description']})"
                    context_lines.append(line)
        
        return "\n".join(context_lines)

    def ask_question(self, question: str):
       
        vector_docs = self.vector_service.query_similar(question)
        vector_context = "\n".join(vector_docs)

       
        graph_context = self.get_graph_context(question)

        # 3. Combine both contexts & Ask Groq
        full_context = f"""
        --- VECTOR CONTEXT (From Text Chunks) ---
        {vector_context}

        --- GRAPH CONTEXT (From Neo4j Relationships) ---
        {graph_context}
        """
        
        system_prompt = """
        You are a helpful AI Assistant backed by a Knowledge Graph.
        Answer the user's question using ONLY the context provided below.
        If the context doesn't have the answer, say "I don't know based on the provided documents."
        """
        
        # Call Groq to generate the final answer
        response = self.llm_service.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{full_context}\n\nQuestion: {question}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1
        )
        
        return {
            "answer": response.choices[0].message.content,
            "context_used": {
                "vector": vector_docs,
                "graph": graph_context.split("\n") if graph_context else []
            }
        }