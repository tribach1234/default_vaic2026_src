# Deal Connect – GitHub Pages + Flask Local + Cloudflare Tunnel

Gói này đã được tách thành hai phần độc lập:

- `github-pages/`: chỉ chứa HTML, JavaScript và ảnh để đưa lên GitHub Pages.
- `local-backend/`: chạy trên máy cá nhân bằng Flask + Waitress; không đưa thư mục này lên repository public.

## Cảnh báo bảo mật bắt buộc

File ZIP ban đầu chứa `.env` có Gemini API key thật và `credentials.json.json` có OAuth client secret. Hãy thu hồi/rotate các thông tin đó trước khi demo. Bản đóng gói mới không chứa hai file này.

## 1. Chuẩn bị backend local

1. Mở `local-backend`.
2. Chạy `install_backend.bat`.
3. Mở file `.env` vừa được tạo.
4. Điền tối thiểu:

```env
GEMINI_API_KEY=API_KEY_MOI
ALLOWED_ORIGINS=https://TEN_GITHUB.github.io
```

Lưu ý: với URL `https://TEN_GITHUB.github.io/TEN_REPO/`, origin vẫn chỉ là `https://TEN_GITHUB.github.io`.

5. Chạy `start_backend.bat`.
6. Kiểm tra bằng PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\test_backend.ps1
```

Backend chỉ lắng nghe tại `127.0.0.1:5000`, không mở port router/firewall ra Internet.

### Tối ưu RAM

Mặc định chỉ xử lý một tác vụ AI nặng cùng lúc:

```env
MAX_CONCURRENT_JOBS=1
MAX_QUEUED_JOBS=3
TOP_MATCHES=5
```

Mô hình `BAAI/bge-m3` được tải lần đầu khi có tác vụ đầu tiên. Lần đầu có thể chậm do tải model; các lần sau dùng lại model và embedding nhà đầu tư trong RAM.

## 2. Tạo Named Cloudflare Tunnel ổn định

Điều kiện: có một domain đang quản lý DNS trên Cloudflare. Nếu không có domain riêng, Quick Tunnel chỉ phù hợp thử nhanh và URL có thể thay đổi.

Trong Cloudflare Dashboard:

1. Vào **Networking → Tunnels**.
2. Tạo tunnel, ví dụ `deal-connect-demo`.
3. Chọn Windows và chạy lệnh cài connector/token mà Dashboard cung cấp bằng CMD/PowerShell Administrator.
4. Thêm **Published application**:
   - Hostname: `api.ten-domain.com`
   - Service type: `HTTP`
   - URL: `127.0.0.1:5000`
5. Chờ tunnel hiện trạng thái Healthy.
6. Mở `https://api.ten-domain.com/api/health` để kiểm tra.

Không cấu hình port forwarding trên modem và không cho Flask lắng nghe `0.0.0.0`.

Cloudflare Tunnel tạo kết nối outbound từ máy local lên Cloudflare. `cloudflared` nên chạy dưới dạng Windows service để tự khởi động cùng hệ thống.

## 3. Cấu hình GitHub Pages frontend

Mở `github-pages/config.js` và sửa:

```javascript
window.APP_CONFIG = {
    API_BASE_URL: "https://api.ten-domain.com",
    DEMO_API_KEY: ""
};
```

Nếu đặt `DEMO_API_KEY` trong backend `.env`, điền cùng giá trị ở đây. Giá trị trong frontend có thể bị xem bởi người dùng, nên đây chỉ là lớp chống quét ngẫu nhiên, không phải secret thật.

Sau đó đưa **nội dung bên trong thư mục `github-pages/`** lên root của repository dùng cho GitHub Pages. Không upload `local-backend`, `.env`, credential hoặc file PDF mẫu.

## 4. Luồng xử lý mới

Frontend không còn giữ một request dài tới khi AI chạy xong:

1. `POST /api/analyze` tải PDF và nhận `job_id` ngay.
2. Frontend gọi `GET /api/jobs/<job_id>` định kỳ.
3. Backend trả tiến độ và kết quả khi hoàn tất.

Thiết kế này tránh lỗi Cloudflare 524 khi tác vụ AI kéo dài hơn thời gian chờ của một request HTTP.

## 5. Cho backend tự chạy khi bật máy

`cloudflared` đã chạy như Windows service. Với backend, tạo Task Scheduler:

- Trigger: **At startup**, delay khoảng 30 giây.
- Action: chạy file `local-backend\start_backend.bat`.
- Chọn **Run whether user is logged on or not**.
- Chọn **Run with highest privileges** nếu chính sách máy yêu cầu.
- Trong Settings, bật tự khởi động lại nếu task lỗi.

## 6. Kiểm tra lỗi

- Badge **Backend Offline**: tunnel/backend chưa chạy, hostname sai hoặc CORS chặn health request.
- HTTP 403: `ALLOWED_ORIGINS` không đúng origin GitHub Pages.
- HTTP 413: file lớn hơn `MAX_UPLOAD_MB`.
- HTTP 429: hàng đợi đầy hoặc vượt rate limit.
- HTTP 502 từ Cloudflare: tunnel không kết nối được `127.0.0.1:5000`.
- Job failed: xem cửa sổ backend để lấy stack trace; frontend cũng hiển thị thông báo lỗi.

## 7. Không đưa lên GitHub public

- `.env`
- `credentials*.json`
- `.venv/`
- `uploads/`
- log, cache Python, model cache
- toàn bộ thư mục `local-backend/` nếu repository frontend là public
