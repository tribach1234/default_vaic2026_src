# prompts.py
from __future__ import annotations


def get_email_prompt(
    startup: dict,
    investor: dict,
    match_score: float,
    match_reason: str,
) -> str:
    startup_name = startup.get("name") or "[Tên Startup]"
    startup_industry = startup.get("industry") or "[Lĩnh vực hoạt động]"
    investor_name = investor.get("name") or "[Tên Quỹ]"

    return f"""
Bạn là chuyên gia viết email gọi vốn cho startup.

Hãy đóng vai Founder của startup "{startup_name}" và viết một cold email gửi tới quỹ đầu tư "{investor_name}".

THÔNG TIN ĐẦU VÀO

Startup:
- Tên startup: {startup_name}
- Lĩnh vực: {startup_industry}

Nhà đầu tư:
- Tên quỹ: {investor_name}

Mức độ phù hợp:
- Điểm tương thích: {match_score}
- Lý do phù hợp: {match_reason}

YÊU CẦU NỘI DUNG

1. Viết bằng tiếng Việt, với giọng văn chuyên nghiệp, tự tin và trực tiếp.
2. Tổng độ dài phần nội dung email từ 150 đến 220 từ.
3. Tiêu đề ngắn gọn, cụ thể và thể hiện rõ cơ hội hợp tác hoặc đầu tư.
4. Mở đầu trực tiếp bằng lời chào gửi tới "{investor_name}".
5. Giới thiệu ngắn gọn startup "{startup_name}" và vấn đề startup đang giải quyết.
6. Làm rõ điểm phù hợp giữa startup và định hướng đầu tư của quỹ dựa trên dữ liệu đầu vào.
7. Không liệt kê điểm tương thích dưới dạng số trong email.
8. Không tự bịa doanh thu, số lượng khách hàng, tốc độ tăng trưởng, số vốn cần gọi hoặc tên Founder.
9. Kết thúc bằng đề nghị một cuộc trao đổi kéo dài 15 phút.
10. Không sử dụng Markdown, không thêm giải thích trước hoặc sau email.

ĐỊNH DẠNG ĐẦU RA BẮT BUỘC

Tiêu đề: [Tiêu đề email]

Kính gửi Đội ngũ Đầu tư {investor_name},

[Nội dung email gồm 3-4 đoạn ngắn, đi thẳng vào trọng tâm.]

Trân trọng,

[Tên Founder]
Founder, {startup_name}

Chỉ trả về email theo đúng định dạng trên. Bắt đầu ngay bằng dòng "Tiêu đề:".
""".strip()


def get_match_reason_prompt(startup: dict, investor: dict) -> str:
    startup_name = startup.get("name", "[Tên Startup]")
    investor_name = investor.get("name", "[Tên Quỹ]")
    technology_score = startup.get("technology", 0)
    problem_score = startup.get("problem", 0)
    thesis_score = startup.get("investment_thesis", 0)
    customer_score = startup.get("customers", 0)

    return f"""
Bạn là chuyên gia phân tích đầu tư tại Trung tâm Đổi mới sáng tạo Quốc gia (NIC).
Viết MỘT đoạn văn ngắn 3-4 câu, dưới 80 từ, giải thích vì sao Startup và Quỹ đầu tư phù hợp.

THÔNG TIN:
- Startup: {startup_name}
- Quỹ đầu tư: {investor_name}
- Công nghệ: {technology_score}
- Vấn đề giải quyết: {problem_score}
- Khẩu vị đầu tư: {thesis_score}
- Tệp khách hàng: {customer_score}

YÊU CẦU:
1. Lấy tiêu chí có điểm cao nhất làm luận điểm chính.
2. Giọng văn phân tích, chuyên nghiệp và thuyết phục.
3. Không bịa số liệu hay thông tin ngoài đầu vào.
4. Chỉ trả về đoạn phân tích, không lời chào, không tiêu đề.
""".strip()


def get_time_extraction_prompt(reply_text: str) -> str:
    return f"""
Bạn là hệ thống trích xuất lịch hẹn.

Đọc phản hồi của startup và trích xuất chính xác thời gian bắt đầu, kết thúc.
- Năm hiện tại: 2026.
- Múi giờ: Việt Nam, UTC+07:00.
- Nếu phản hồi chỉ nêu giờ bắt đầu, mặc định cuộc họp kéo dài 60 phút.

PHẢN HỒI:
{reply_text}

Chỉ trả về JSON hợp lệ, không Markdown, đúng cấu trúc:
{{
  "start_time_iso": "YYYY-MM-DDTHH:MM:00+07:00",
  "end_time_iso": "YYYY-MM-DDTHH:MM:00+07:00"
}}
""".strip()


def get_mock_startup_reply_prompt(
    start_time_str: str,
    end_time_str: str,
    date_str: str,
    investor_name: str = "quỹ đầu tư",
) -> str:
    return f"""
Đóng vai Founder của một startup đang xác nhận lịch họp với "{investor_name}".

Khung giờ đã chọn:
- Từ {start_time_str} đến {end_time_str}
- Ngày {date_str}
- Múi giờ Việt Nam (UTC+07:00)

Viết đúng MỘT câu phản hồi ngắn gọn, lịch sự và tự nhiên để xác nhận khung giờ này.
Không viết tiêu đề, không Markdown, không thêm giải thích.
""".strip()
