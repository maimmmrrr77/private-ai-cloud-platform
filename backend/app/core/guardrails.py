import re
from typing import Tuple

# Danh sách các mẫu tấn công Prompt Injection phổ biến
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"bỏ\s+qua\s+(tất\s+cả\s+)?các\s+chỉ\s+dẫn\s+trước",
    r"forget\s+everything",
    r"quên\s+hết\s+quy\s+tắc",
    r"system\s+prompt",
    r"act\s+as\s+a\s+jailbreak",
    r"you\s+are\s+now\s+dan"
]

def check_prompt_injection(text: str) -> Tuple[bool, str]:
    """
    Kiểm tra xem câu hỏi có chứa dấu hiệu tấn công Prompt Injection hay không.
    Trả về: (is_safe, message)
    """
    lower_text = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower_text):
            return False, "⚠️ Cảnh báo bảo mật: Phát hiện hành vi cố gắng vượt rào hệ thống (Prompt Injection)."
    return True, "OK"

def mask_pii(text: str) -> str:
    """
    Che giấu thông tin định danh cá nhân (PII) trước khi gửi qua LLM:
    - Số CCCD / CMND (9 hoặc 12 số)
    - Số điện thoại Việt Nam
    - Địa chỉ Email
    """
    # 1. Che giấu Email
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL_HIDDEN]', text)
    
    # 2. Che giấu Số điện thoại VN (03x, 05x, 07x, 08x, 09x hoặc +84)
    text = re.sub(r'(\+84|0)(3|5|7|8|9)[0-9]{8}\b', '[PHONE_HIDDEN]', text)
    
    # 3. Che giấu Số CCCD (12 chữ số) hoặc CMND (9 chữ số)
    text = re.sub(r'\b\d{12}\b', '[CCCD_HIDDEN]', text)
    text = re.sub(r'\b\d{9}\b', '[CMND_HIDDEN]', text)
    
    return text

def validate_and_sanitize_input(user_query: str) -> Tuple[bool, str]:
    """Hàm tổng hợp kiểm tra an toàn và lọc PII."""
    is_safe, msg = check_prompt_injection(user_query)
    if not is_safe:
        return False, msg
    
    sanitized_query = mask_pii(user_query)
    return True, sanitized_query