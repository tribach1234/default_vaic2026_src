# prompts.py

def get_email_prompt(
    startup: dict,
    investor: dict,
    match_score: float,
    match_reason: str
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
        3. Tiêu đề phải ngắn gọn, cụ thể và thể hiện rõ cơ hội hợp tác hoặc cơ hội đầu tư.
        4. Mở đầu email trực tiếp bằng lời chào gửi tới "{investor_name}".
        5. Giới thiệu ngắn gọn startup "{startup_name}" và vấn đề startup đang giải quyết.
        6. Làm rõ điểm phù hợp giữa startup và định hướng đầu tư của "{investor_name}", dựa trên lý do phù hợp đã cung cấp.
        7. Không liệt kê lại điểm tương thích dưới dạng số.
        8. Không viết những nhận định chung chung như:
        - "đây là một cơ hội tuyệt vời"
        - "chúng tôi tin rằng hai bên có nhiều điểm tương đồng"
        - "startup đầy tiềm năng"
        Trừ khi có thông tin cụ thể hỗ trợ.
        9. Kết thúc bằng một lời đề nghị rõ ràng về cuộc trao đổi kéo dài 15 phút.
        10. Không tự bịa doanh thu, số lượng khách hàng, tốc độ tăng trưởng, số vốn cần gọi hoặc tên Founder nếu dữ liệu đầu vào không có.
        11. Nếu thiếu tên Founder, sử dụng chữ ký "[Tên Founder]".
        12. Không sử dụng Markdown, không dùng dấu **, dấu # hoặc khối mã.
        13. Không thêm lời giới thiệu, lời giải thích, nhận xét hoặc ghi chú trước và sau email.
        14. Không được viết các câu như:
        - "Chào bạn"
        - "Dưới đây là mẫu email"
        - "Tôi đã soạn email"
        - "Bạn có thể tham khảo"
        - "Hy vọng email này hữu ích"

        ĐỊNH DẠNG ĐẦU RA BẮT BUỘC

        Tiêu đề: [Tiêu đề email]

        Kính gửi Đội ngũ Đầu tư {investor_name},

        [Đoạn 1: Giới thiệu ngắn gọn Founder, startup và vấn đề đang giải quyết.]

        [Đoạn 2: Trình bày giải pháp, giá trị nổi bật và thị trường mục tiêu dựa trên dữ liệu được cung cấp.]

        [Đoạn 3: Nêu cụ thể lý do startup phù hợp với định hướng đầu tư của quỹ. Không nhắc đến thuật ngữ "AI Match" hoặc "điểm matching".]

        [Đoạn 4: Đề nghị một cuộc trao đổi 15 phút và đưa ra bước tiếp theo rõ ràng.]

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
    return f"""Bạn là một chuyên gia phân tích đầu tư lõi lõi tại Trung tâm Đổi mới sáng tạo Quốc gia (NIC).
Nhiệm vụ của bạn là viết MỘT đoạn văn ngắn gọn (khoảng 3-4 câu, dưới 80 từ) giải thích lý do tại sao Startup và Quỹ đầu tư này lại phù hợp với nhau.

THÔNG TIN ĐẦU VÀO:
- Tên Startup: {startup_name}
- Tên Quỹ đầu tư: {investor_name}

ĐIỂM ĐÁNH GIÁ ĐỘ KHỚP THEO TIÊU CHÍ (0.0 đến 1.0):
- Công nghệ (Technology Focus): {technology_score}
- Vấn đề giải quyết (Problem Focus): {problem_score}
- Khẩu vị đầu tư (Investment Thesis): {thesis_score}
- Tệp khách hàng (Customer Focus): {customer_score}

YÊU CẦU BẮT BUỘC (RULE-BASED):
1. Phân tích trọng tâm: Tìm tiêu chí có điểm số cao nhất trong 4 tiêu chí trên và lấy đó làm luận điểm chính để giải thích sự phù hợp.
2. Logic & Chuyên nghiệp: Giọng văn mang tính phân tích sắc bén, thuyết phục, dùng từ ngữ chuyên ngành đầu tư khởi nghiệp.
3. Chống ảo giác (No Hallucination): Ttuyệt đối KHÔNG bịa đặt thêm số liệu tài chính hay thông tin không có trong đầu vào.
4. Định dạng đầu ra: Trả về TRỰC TIẾP đoạn văn phân tích, KHÔNG có lời chào, KHÔNG có tiêu đề, KHÔNG giải thích lôi thôi.
"""