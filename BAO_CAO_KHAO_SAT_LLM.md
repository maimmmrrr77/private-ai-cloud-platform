# BÁO CÁO KHẢO SÁT LỰA CHỌN MÔ HÌNH LLM & BỘ DỮ LIỆU MẪU
**Dự án:** Private AI cloud & internal LLM platform for legal enterprise
**Người thực hiện:** Nguyễn Thị Ngọc Mai (B22DCCN517)
**Thời gian:** Tuần 1

---

## 1. KHẢO SÁT VÀ LỰA CHỌN MÔ HÌNH NGÔN NGỮ LỚN (LLM)

### 1.1 Yêu cầu kỹ thuật & Môi trường triển khai
- **Khả năng hiểu tiếng Việt & Pháp lý:** Phân tích chính xác câu hỏi pháp lý và điều khoản luật.
- **Tính riêng tư & Air-gapped:** Vận hành 100% On-premise, không truyền dữ liệu ra Internet.
- **Cấu trúc môi trường triển khai song song:**
  1. **Môi trường Dev & Local Testing (Máy cá nhân - CPU/RAM):** Yêu cầu mô hình nhẹ (~1.5B - 3B params), đã nén Quantized (GGUF/INT4), chạy mượt qua Ollama/llama.cpp không cần GPU rời.
  2. **Môi trường Staging & Production (Server K3s / GPU On-premise):** Sử dụng mô hình chất lượng cao (~7B - 14B params) phục vụ đa người dùng qua vLLM Serving.

### 1.2 So sánh các mô hình LLM nguồn mở
| Bảng tiêu chí | Qwen2.5-3B-Instruct (GGUF) | Qwen2.5-7B-Instruct | PhoGPT-4B-Chat | Vistral-7B-Chat |
| :--- | :--- | :--- | :--- | :--- |
| **Mục đích sử dụng** | **Local Dev & Testing (CPU)** | **Server Production (GPU)** | Tham khảo | Tham khảo |
| **Dung lượng File** | ~1.9 GB | ~14 GB (FP16) / ~5.5 GB (INT4) | ~2.5 GB | ~14 GB |
| **Yêu cầu RAM/VRAM** | ~4 GB RAM (Chạy CPU) | ~14GB VRAM (vLLM) | ~6 GB RAM | ~14GB VRAM |
| **Context Window** | 32k tokens | 32k - 128k tokens | 2k - 4k tokens | 8k - 32k tokens |
| **Tương thích Ollama / vLLM** | Rất mượt trên Ollama CPU | Rất mượt trên vLLM GPU | Cần tùy biến | Hỗ trợ tốt |

### 1.3 Đề xuất lựa chọn mô hình chính thức
- **Môi trường Local Dev (Laptop cá nhân):** 
  - Mô hình LLM: `qwen2.5:3b` (Quantized GGUF chạy qua **Ollama**).
  - *Lý do:* Chạy phản hồi cực nhanh trên CPU/RAM Laptop, tiết kiệm tài nguyên, hỗ trợ tiếng Việt xuất sắc để phát triển Back-end RAG và kiểm thử giao diện UI.
- **Môi trường Server GPU (Hạ tầng K3s Production):** 
  - Mô hình LLM: `Qwen2.5-7B-Instruct` (Deploy qua **vLLM / Ollama**).
  - *Lý do:* Đảm bảo độ chính xác pháp lý cao nhất, suy luận song song nhiều request.
- **Mô hình nhúng Vector (Embedding Model - Dùng chung):** 
  - `bkai-foundation-models/vietnamese-bi-encoder` (hoặc `BAAI/bge-m3`).
  - *Lý do:* Dung lượng nhẹ (~500MB), chạy rất tốt trên CPU bằng thư viện `sentence-transformers`, biểu diễn ngữ nghĩa tiếng Việt và thuật ngữ pháp lý chính xác.

---

## 2. CHUẨN BỊ BỘ DỮ LIỆU PHÁP LÝ MẪU

### 2.1 Danh mục tài liệu thu thập
Các văn bản pháp quy đã thu thập và lưu trữ tại thư mục `data/sample_documents/`:
1. `Luat_Doanh_nghiep_2020.pdf` - Quy định về thành lập, tổ chức quản lý doanh nghiệp.
2. `Bo_luat_Lao_dong_2019.pdf` - Quy định về hợp đồng lao động, thời giờ làm việc, nghỉ ngơi.
3. `Bo_luat_Dan_su_2015.pdf` - Quy định về giao dịch dân sự, hợp đồng, nghĩa vụ tài sản.
4. `Mau_Hop_dong_Lao_dong.docx` - Mẫu hợp đồng chuẩn dùng cho kiểm thử trích xuất & che giấu thông tin cá nhân (PII Masking).

### 2.2 Kế hoạch xử lý dữ liệu (Tuần 2)
- **Định dạng file hỗ trợ:** `.pdf`, `.docx`.
- **Phương pháp Chunking dự kiến:** Đoạn văn bản kích thước ~512 tokens, độ đè phủ (overlap) 50 tokens.
- **Lưu trữ:** Lưu file gốc tại MinIO Object Storage và Vector Embedding tại Qdrant DB.