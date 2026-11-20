from fastapi import FastAPI
from app.api import chat, auth, documents
from app.models.database import init_db, SessionLocal, User
from app.core.security import get_password_hash

app = FastAPI(
    title="Private AI Cloud - Legal RAG API",
    description="API hệ thống trợ lý AI pháp lý nội bộ tích hợp RAG, Guardrails, RBAC & Quản lý tri thức",
    version="1.1.0"
)

# Khởi tạo Database và tạo sẵn 1 tài khoản Admin mặc định để test
@app.on_event("startup")
def on_startup():
    init_db()
    db = SessionLocal()
    if not db.query(User).filter(User.username == "admin").first():
        admin_user = User(
            username="admin",
            full_name="Quản trị viên Hệ thống",
            hashed_password=get_password_hash("admin123"),
            role="admin"
        )
        db.add(admin_user)
        db.commit()
    db.close()

# Đăng ký đầy đủ 3 nhóm Router (Chat RAG, Auth/RBAC, Quản lý tài liệu)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)

@app.get("/")
def health_check():
    return {"status": "online", "message": "Private AI RAG Backend (Week 4) is running!"}