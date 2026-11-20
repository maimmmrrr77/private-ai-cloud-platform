from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.guardrails import validate_and_sanitize_input
from app.services.rag_engine import generate_rag_response

router = APIRouter(prefix="/api/v1/chat", tags=["RAG Chatbot"])

class ChatRequest(BaseModel):
    question: str

@router.post("/query")
async def ask_legal_assistant(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Câu hỏi không được để trống.")
    
    # Bước 1: Kiểm tra Guardrails & Lọc PII (Nhiệm vụ 3.4)
    is_valid, result_text = validate_and_sanitize_input(request.question)
    if not is_valid:
        raise HTTPException(status_code=403, detail=result_text)
    
    # Bước 2: Chạy Core RAG Engine (Nhiệm vụ 3.3)
    rag_result = generate_rag_response(sanitized_query=result_text)
    
    return {
        "status": "success",
        "data": rag_result
    }