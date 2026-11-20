from fastapi import FastAPI
from app.api import chat

app = FastAPI(
    title="Private AI Cloud - Legal RAG API",
    description="API hệ thống trợ lý AI pháp lý nội bộ tích hợp RAG và Guardrails",
    version="1.0.0"
)

# Đăng ký Router
app.include_router(chat.router)

@app.get("/")
def health_check():
    return {"status": "online", "message": "Private AI RAG Backend is running!"}