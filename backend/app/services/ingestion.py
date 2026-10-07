import os
from pathlib import Path
from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Tích hợp PyMuPDF (fitz)
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

def extract_text_from_pdf(file_path: str) -> str:
    """Trích xuất văn bản từ file PDF sử dụng PyMuPDF (hoặc fallback)."""
    text = ""
    if HAS_FITZ:
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")
            if page_text:
                text += f"\n--- Trang {page_num + 1} ---\n" + page_text
        doc.close()
    else:
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Trang {page_num + 1} ---\n" + page_text
        except ImportError:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Trang {page_num + 1} ---\n" + page_text
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Trích xuất văn bản từ file Word (.docx)."""
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text)
    return "\n".join(full_text)

def clean_text(text: str) -> str:
    """Làm sạch văn bản thô, bảo toàn cấu trúc xuống dòng."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)

def chunk_document(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Cắt nhỏ văn bản thành các chunks phù hợp ngữ cảnh tiếng Việt."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "Điều ", "Khoản ", ". ", " ", ""]
    )
    return text_splitter.split_text(text)

def process_file(file_path: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Hàm tổng hợp: Tiếp nhận đường dẫn file -> Đọc -> Làm sạch -> Cắt chunks."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file tài liệu tại: {file_path}")

    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        raw_text = extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        raw_text = extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Định dạng file '{ext}' chưa được hỗ trợ hệ thống.")
    
    cleaned = clean_text(raw_text)
    if not cleaned:
        return []
        
    return chunk_document(cleaned, chunk_size=chunk_size, chunk_overlap=chunk_overlap)