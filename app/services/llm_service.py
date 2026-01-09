import json
from groq import Groq
from app.config import settings

class LLMService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def extract_graph_data(self, text: str):
        """
        Uses Groq (Llama3/Mixtral) to extract entities and relationships.
        """
       
        safe_text = text[:6000] 

        system_prompt = """
        You are a top-tier Knowledge Graph Engineer.
        Your task is to extract information from the given text and structure it into a JSON format for Neo4j.
        
        Rules:
        1. Identify key **Entities** (nodes) and **Relationships** (edges).
        2. Entities must have a 'id' (unique name), 'type' (e.g., PERSON, ORG, CONCEPT), and 'description'.
        3. Relationships must have 'source', 'target', 'type' (verb), and 'description'.
        4. Output strictly valid JSON. No markdown, no conversational text.
        
        JSON Structure:
        {
          "entities": [{"id": "...", "type": "...", "description": "..."}],
          "relationships": [{"source": "...", "target": "...", "type": "...", "description": "..."}]
        }
        """

        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract knowledge from this text:\n\n{safe_text}"}
                ],
                model="llama-3.3-70b-versatile", 
                temperature=0,          
                response_format={"type": "json_object"} 
            )
            
            result = completion.choices[0].message.content
            return json.loads(result)

        except Exception as e:
            print(f"Groq API Error: {e}")
            return {"entities": [], "relationships": [], "error": str(e)}