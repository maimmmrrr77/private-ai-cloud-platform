import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

from app.models.database import get_db, LegalDocument, User
from app.core.security import get_current_user, require_admin
from app.services.ingestion import process_file
from app.services.rag_engine import qdrant_client, embedding_model, COLLECTION_NAME

router = APIRouter(prefix="/api/v1/documents", tags=["Document Management & Embedding"])

UPLOAD_DIR = "local_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_and_embed_document(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),  # Chỉ Admin được nạp tri thức
    db: Session = Depends(get_db)
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ định dạng PDF hoặc Word (.docx)")

    # 1. Lưu file gốc vào thư mục local (Thay cho MinIO khi chưa có server)
    saved_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Đọc, làm sạch, cắt chunks và tạo Vector Embedding
    try:
        chunks = process_file(saved_path)
        if not chunks:
            raise ValueError("Không trích xuất được nội dung văn bản từ tệp.")

        vectors = embedding_model.encode(chunks).tolist()
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vectors[i],
                payload={
                    "text": chunks[i],
                    "source_file": file.filename,
                    "chunk_id": i
                }
            )
            for i in range(len(chunks))
        ]
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
        status_str = "embedded"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý Embedding tài liệu: {str(e)}")

    # 3. Lưu Metadata vào Database (SQLite/PostgreSQL)
    doc_record = LegalDocument(
        filename=file.filename,
        file_path=saved_path,
        status=status_str,
        chunk_count=len(chunks),
        uploaded_by=current_user.username
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    return {
        "message": "Tải lên và kích hoạt Embedding thành công!",
        "document": {
            "id": doc_record.id,
            "filename": doc_record.filename,
            "chunks_indexed": doc_record.chunk_count,
            "status": doc_record.status
        }
    }

@router.get("/")
def list_documents(
    current_user: User = Depends(get_current_user),  # Cả Admin và User đều xem được danh sách
    db: Session = Depends(get_db)
):
    docs = db.query(LegalDocument).order_by(LegalDocument.uploaded_at.desc()).all()
    return docs

@router.delete("/{doc_id}", dependencies=[Depends(require_admin)])
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(LegalDocument).filter(LegalDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")

    # 1. Xóa các vector tương ứng trong Qdrant DB
    try:
        qdrant_client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[FieldCondition(key="source_file", match=MatchValue(value=doc.filename))]
            )
        )
    except Exception as e:
        print(f"⚠️ Cảnh báo khi xóa vector trên Qdrant: {e}")

    # 2. Xóa file vật lý
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    # 3. Xóa bản ghi trong Database
    db.delete(doc)
    db.commit()
    return {"message": f"Đã xóa hoàn toàn tài liệu '{doc.filename}' và dữ liệu vector liên quan."}