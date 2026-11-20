import os
from typing import List, Dict, Any
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# Cấu hình kết nối (Mặc định trỏ về Local để test, khi có Server thì đổi qua biến môi trường)
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "legal_knowledge_base"

# Endpoint LLM (Ollama local dùng cổng 11434/v1, vLLM server dùng cổng 8000/v1)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "not-needed")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "qwen2.5:3b") # Đổi thành Qwen/Qwen2.5-7B-Instruct khi nối server

# Tải mô hình Embedding tiếng Việt từ Tuần 2
EMBEDDING_MODEL_NAME = "bkai-foundation-models/vietnamese-bi-encoder"
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# Khởi tạo Client kết nối Qdrant và LLM
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
llm_client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

def retrieve_relevant_chunks(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Bước 1 của RAG: Tìm kiếm Top-K đoạn văn bản liên quan trong Qdrant DB."""
    query_vector = embedding_model.encode([query])[0].tolist()
    
    try:
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k
        )
        contexts = []
        for hit in search_results:
            contexts.append({
                "text": hit.payload.get("text", ""),
                "source_file": hit.payload.get("source_file", "Không rõ nguồn"),
                "chunk_id": hit.payload.get("chunk_id", 0),
                "score": round(hit.score, 4)
            })
        return contexts
    except Exception as e:
        print(f"⚠️ Lỗi kết nối Qdrant: {e}")
        return []

def build_rag_prompt(query: str, contexts: List[Dict[str, Any]]) -> str:
    """Bước 2 của RAG: Lắp ghép ngữ cảnh pháp lý vào Prompt."""
    if not contexts:
        context_str = "Không tìm thấy tài liệu pháp lý liên quan trong cơ sở dữ liệu."
    else:
        context_str = "\n\n".join([
            f"[Tài liệu: {c['source_file']} - Đoạn {c['chunk_id']}]:\n{c['text']}"
            for c in contexts
        ])

    prompt = f"""Bạn là trợ lý AI pháp lý nội bộ chuyên nghiệp. Hãy trả lời câu hỏi của người dùng CHỈ DỰA TRÊN các tài liệu tham khảo được cung cấp dưới đây.
Nếu thông tin không có trong tài liệu, hãy nói rõ "Tôi không tìm thấy thông tin này trong tài liệu nội bộ", tuyệt đối không tự suy diễn.
Luôn trích dẫn tên tài liệu nguồn ở cuối câu trả lời.

--- TÀI LIỆU THAM KHẢO ---
{context_str}
---------------------------

Câu hỏi của người dùng: {query}
Trả lời:"""
    return prompt

def generate_rag_response(sanitized_query: str) -> Dict[str, Any]:
    """Luồng xử lý RAG hoàn chỉnh: Retrieval -> Prompt -> LLM Generation."""
    # 1. Truy xuất tri thức
    retrieved_docs = retrieve_relevant_chunks(sanitized_query, top_k=3)
    
    # 2. Tạo Prompt
    final_prompt = build_rag_prompt(sanitized_query, retrieved_docs)
    
    # 3. Gọi LLM sinh câu trả lời
    try:
        response = llm_client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": "Bạn là trợ lý pháp lý AI chính xác và bảo mật."},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.2 # Giảm nhiệt độ để câu trả lời bám sát luật, hạn chế ảo giác
        )
        answer = response.choices[0].message.content
    except Exception as e:
        answer = f"⚠️ Lỗi kết nối đến LLM Serving ({LLM_BASE_URL}): {str(e)}"

    return {
        "sanitized_query": sanitized_query,
        "answer": answer,
        "citations": retrieved_docs
    }