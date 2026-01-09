from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_service import PDFService
from app.services.llm_service import LLMService
from app.services.graph_service import GraphService
from app.services.vector_service import VectorService
from app.services.rag_service import RAGService # <--- Import the new service
from pydantic import BaseModel

router = APIRouter()
pdf_service = PDFService()
llm_service = LLMService()
graph_service = GraphService()
vector_service = VectorService()
rag_service = RAGService()


# Define the request body format
class QuestionRequest(BaseModel):
    question: str

@router.post("/ask-question")
async def ask_question(request: QuestionRequest):
    """
    Hybrid RAG Query: Uses both Vector Search + Graph Relationships
    """
    if not request.question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    response = rag_service.ask_question(request.question)
    
    return response


@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    # 1. Save & Extract
    file_path = await pdf_service.save_pdf(file)
    raw_text = pdf_service.extract_text(file_path)

    # 2. AI Extraction
    graph_data = llm_service.extract_graph_data(raw_text)

    # 3. Build Graph (Neo4j)
    try:
        graph_service.build_graph(graph_data)
    except Exception as e:
        print(f"Graph Error: {e}")

    # 4. Vectorize (ChromaDB) - NEW STEP
    try:
        num_chunks = vector_service.add_texts(raw_text, file.filename)
    except Exception as e:
        print(f"Vector Error: {e}")
        num_chunks = 0

    return {
        "filename": file.filename,
        "status": "Phase 4 Complete (Graph + Vectors)",
        "graph_nodes": len(graph_data.get("entities", [])),
        "vector_chunks": num_chunks,  # <--- Confirming chunks stored
        "next_step": "Ready for RAG Queries"
    }