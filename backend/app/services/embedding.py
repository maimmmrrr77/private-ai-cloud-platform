import os
import uuid
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from app.services.ingestion import process_file

# Cấu hình kết nối hệ thống
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "legal_knowledge_base")
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "bkai-foundation-models/vietnamese-bi-encoder")

# Khởi tạo singleton Embedding Model & Qdrant Client
embedding_model = SentenceTransformer(MODEL_NAME)
VECTOR_SIZE = embedding_model.get_sentence_embedding_dimension()
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

def init_qdrant_collection(collection_name: str = COLLECTION_NAME):
    """Khởi tạo Collection trên Qdrant Database nếu chưa tồn tại."""
    collections = [c.name for c in qdrant_client.get_collections().collections]
    if collection_name not in collections:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Tạo Vector Embeddings cho danh sách chuỗi văn bản."""
    embeddings = embedding_model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()

def index_document_to_qdrant(file_path: str, extra_metadata: Dict[str, Any] = None) -> int:
    """
    Pipeline chính: Đọc file -> Cắt Chunks -> Embed -> Nạp vào Qdrant DB.
    Trả về số lượng chunks đã được lưu thành công.
    """
    init_qdrant_collection()
    
    # 1. Xử lý cắt chunks từ file
    chunks = process_file(file_path)
    if not chunks:
        return 0

    # 2. Tạo Vector Embeddings
    vectors = generate_embeddings(chunks)

    # 3. Đóng gói PointStruct kèm Payload Metadata
    filename = os.path.basename(file_path)
    points = []
    for idx, (chunk_text, vector) in enumerate(zip(chunks, vectors)):
        payload = {
            "text": chunk_text,
            "source_file": filename,
            "chunk_id": idx,
            "total_chunks": len(chunks)
        }
        if extra_metadata:
            payload.update(extra_metadata)

        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=payload
            )
        )

    # 4. Upsert vào Qdrant Database
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)

def search_similar_chunks(query: str, top_k: int = 5, collection_name: str = COLLECTION_NAME) -> List[Dict[str, Any]]:
    """Truy vấn tìm kiếm Top-K các đoạn văn bản tương đồng theo câu hỏi."""
    query_vector = generate_embeddings([query])[0]
    
    response = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=top_k
    )
    
    results = []
    for point in response.points:
        results.append({
            "score": point.score,
            "text": point.payload.get("text", ""),
            "source_file": point.payload.get("source_file", ""),
            "chunk_id": point.payload.get("chunk_id", 0)
        })
    return results