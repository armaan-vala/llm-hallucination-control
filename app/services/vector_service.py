import chromadb
from chromadb.utils import embedding_functions
from app.config import settings
import uuid

class VectorService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
        
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection = self.client.get_or_create_collection(
            name="pdf_knowledge",
            embedding_function=self.embedding_fn
        )

    def chunk_text(self, text: str, chunk_size: int = 500):
        """
        Simple splitter: Breaks text into chunks of ~500 chars.
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1
            
            if current_length >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    def add_texts(self, text: str, source_filename: str):
        """
        Chunks the text and stores it in ChromaDB.
        """
        chunks = self.chunk_text(text)
        
        ids = [f"{source_filename}_{i}_{str(uuid.uuid4())[:8]}" for i in range(len(chunks))]
        metadatas = [{"source": source_filename, "chunk_index": i} for i in range(len(chunks))]
        
        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        
        return len(chunks)

    def query_similar(self, question: str, n_results: int = 3):
        """
        Finds the top 3 most relevant chunks for a question.
        """
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results
        )
        return results["documents"][0]