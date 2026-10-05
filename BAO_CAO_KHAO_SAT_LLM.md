# BÁO CÁO KHẢO SÁT LỰA CHỌN MÔ HÌNH LLM & BỘ DỮ LIỆU MẪU
**Dự án:** Private AI cloud & internal LLM platform for legal enterprise
**Người thực hiện:** Nguyễn Thị Ngọc Mai (B22DCCN517)
**Thời gian:** Tuần 1

---

## 1. KHẢO SÁT VÀ LỰA CHỌN MÔ HÌNH NGÔN NGỮ LỚN (LLM)

### 1.1 Yêu cầu kỹ thuật đối với LLM
- **Khả năng hiểu tiếng Việt & Pháp lý:** Phân tích chính xác câu hỏi pháp lý và điều khoản luật.
- **Triển khai Air-gapped / On-premise:** Vận hành hoàn toàn nội bộ trên hạ tầng K3s / GPU doanh nghiệp, không gửi dữ liệu ra ngoài Internet.
- **Tối ưu suy luận:** Tương thích tốt với các công cụ Serving như vLLM / Ollama, hỗ trợ vRAM giới hạn.

### 1.2 So sánh các mô hình LLM nguồn mở
| Bảng tiêu chí | Qwen2.5-7B / 14B-Instruct | PhoGPT-4B-Chat | Vistral-7B-Chat |
| :--- | :--- | :--- | :--- |
| **Nhà phát triển** | Alibaba Cloud | VinAI | VietAI |
| **Hỗ trợ Tiếng Việt** | Rất tốt | Tốt (Chuyên tiếng Việt) | Tốt |
| **Context Window** | 32k - 128k tokens | 2k - 4k tokens | 8k - 32k tokens |
| **Khả năng suy luận & RAG** | Xuất sắc (Ít bị ảo giác) | Trung bình | Khá |
| **Dung lượng VRAM yêu cầu** | ~14GB - 18GB (FP16/INT4) | ~8GB - 10GB | ~14GB |
| **Tương thích vLLM / Ollama** | Hỗ trợ chính thức | Cần tùy biến | Hỗ trợ tốt |

### 1.3 Đề xuất lựa chọn
- **Mô hình suy luận chính (LLM):** `Qwen2.5-7B-Instruct` (hoặc bản Quantized `Qwen2.5-7B-Instruct-GGUF` / `AWQ`).
  - *Lý do:* Context window lớn giúp tiếp nhận nhiều đoạn văn bản trích dẫn RAG; khả năng lập luận tiếng Việt và định dạng đầu ra (JSON / Markdown / Citations) vượt trội.
- **Mô hình nhúng Vector (Embedding Model):** `bkai-foundation-models/vietnamese-bi-encoder` hoặc `bge-m3`.
  - *Lý do:* Tối ưu hóa biểu diễn không gian ngữ nghĩa cho tiếng Việt, tạo vector 1024-1536 chiều tương thích tốt với Qdrant Vector DB.

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