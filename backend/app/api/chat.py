from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.guardrails import validate_and_sanitize_input
from app.services.rag_engine import generate_rag_response
import asyncio
import json
from fastapi.responses import StreamingResponse

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
@router.post("/stream")
async def stream_legal_assistant(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Câu hỏi không được để trống.")

    # Bước 1: Kiểm tra Guardrails & Lọc PII (Nhiệm vụ 3.4)
    is_valid, result_text = validate_and_sanitize_input(request.question)
    if not is_valid:
        raise HTTPException(status_code=403, detail=result_text)

    # Bước 2: Lấy kết quả từ Core RAG Engine
    rag_result = generate_rag_response(sanitized_query=result_text)
    answer_text = rag_result.get("answer", "")
    citations = rag_result.get("citations", [])

    async def event_generator():
        # Gửi thông tin câu hỏi đã ẩn PII và trích dẫn trước
        meta_payload = {
            "type": "meta",
            "sanitized_query": result_text,
            "citations": citations
        }
        yield f"data: {json.dumps(meta_payload, ensure_ascii=False)}\n\n"

        # Stream từng từ (token) tạo hiệu ứng phản hồi real-time
        words = answer_text.split(" ")
        for word in words:
            chunk_payload = {"type": "token", "content": word + " "}
            yield f"data: {json.dumps(chunk_payload, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.03)

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")