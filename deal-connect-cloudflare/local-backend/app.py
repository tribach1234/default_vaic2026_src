import json
import logging
import os
import shutil
import tempfile
import threading
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pdfplumber
from flask import Flask, jsonify, request
from flask_cors import CORS
from google import genai
from google.genai import types
from gemini_client import create_gemini_client
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from calendar_api import register_calendar_routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("deal-connect")

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_UPLOAD_MB * 1024 * 1024

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": Config.ALLOWED_ORIGINS,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "X-Demo-Key"],
            "max_age": 3600,
        }
    },
)

# Đăng ký API đặt lịch demo:
# POST /api/calendar/schedule
register_calendar_routes(app)

UPLOAD_DIR = Config.BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

JOBS: dict[str, dict[str, Any]] = {}
JOBS_LOCK = threading.Lock()
EXECUTOR = ThreadPoolExecutor(
    max_workers=Config.MAX_CONCURRENT_JOBS,
    thread_name_prefix="pdf-job",
)
SUBMISSIONS: dict[str, deque[float]] = defaultdict(deque)
SUBMISSIONS_LOCK = threading.Lock()

RESOURCE_LOCK = threading.Lock()
INVESTORS = None
INVESTOR_EMBEDDINGS = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def client_ip() -> str:
    return request.headers.get("CF-Connecting-IP") or request.remote_addr or "unknown"


def set_job(job_id: str, **updates: Any) -> None:
    with JOBS_LOCK:
        if job_id in JOBS:
            JOBS[job_id].update(updates)
            JOBS[job_id]["updated_at"] = utc_now_iso()


def cleanup_old_jobs() -> None:
    cutoff = time.time() - Config.JOB_TTL_MINUTES * 60
    with JOBS_LOCK:
        expired = [
            job_id
            for job_id, job in JOBS.items()
            if job.get("finished_timestamp", float("inf")) < cutoff
        ]
        for job_id in expired:
            JOBS.pop(job_id, None)


def rate_limit_allows(ip_address: str) -> bool:
    now = time.time()
    cutoff = now - Config.RATE_LIMIT_WINDOW_MINUTES * 60
    with SUBMISSIONS_LOCK:
        bucket = SUBMISSIONS[ip_address]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= Config.RATE_LIMIT_JOBS:
            return False
        bucket.append(now)
        return True


def active_job_count() -> int:
    with JOBS_LOCK:
        return sum(job.get("status") in {"queued", "running"} for job in JOBS.values())


def validate_origin() -> tuple[dict, int] | None:
    origin = request.headers.get("Origin", "").rstrip("/")
    if origin and origin not in Config.ALLOWED_ORIGINS:
        return {"error": "Origin không được phép truy cập API"}, 403
    return None


def validate_demo_key() -> tuple[dict, int] | None:
    if Config.DEMO_API_KEY and request.headers.get("X-Demo-Key", "") != Config.DEMO_API_KEY:
        return {"error": "Demo API key không hợp lệ"}, 401
    return None


@app.before_request
def protect_api():
    if not request.path.startswith("/api/"):
        return None

    origin_error = validate_origin()
    if origin_error:
        return jsonify(origin_error[0]), origin_error[1]

    key_error = validate_demo_key()
    if key_error:
        return jsonify(key_error[0]), key_error[1]

    return None


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@app.errorhandler(RequestEntityTooLarge)
def too_large(_error):
    return jsonify({"error": f"File vượt quá {Config.MAX_UPLOAD_MB} MB"}), 413


@app.get("/")
def root():
    return jsonify(
        {
            "service": "Deal Connect API",
            "status": "online",
            "health": "/api/health",
            "calendar_schedule": "/api/calendar/schedule",
        }
    )


@app.get("/api/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "gemini_configured": bool(Config.GEMINI_API_KEY),
            "allowed_origins": Config.ALLOWED_ORIGINS,
            "active_jobs": active_job_count(),
            "max_active_jobs": Config.MAX_QUEUED_JOBS,
            "calendar_scheduling": True,
        }
    )


def process_pitchdeck(pdf_path: Path) -> str:
    extracted_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                extracted_text.append(text)
    return "\n".join(extracted_text)


def extract_startup_with_gemini(raw_text: str) -> dict | list[dict]:
    prompt = f"""
Bạn là chuyên gia phân tích quỹ đầu tư mạo hiểm. Hãy đọc Pitch Deck và trả về DUY NHẤT JSON hợp lệ, không markdown.

Cấu trúc bắt buộc:
{{
  "name": "Tên dự án",
  "industry": "EdTech/FinTech/AgriTech/HealthTech/...",
  "stage": "Seed/Pre-Series A/Series A/...",
  "funding": 500000,
  "technology": "Công nghệ lõi",
  "problem": "Vấn đề thị trường",
  "solution": "Giải pháp",
  "customers": "Khách hàng mục tiêu",
  "summary": "Tóm tắt 1-2 câu"
}}

Nội dung Pitch Deck:
{raw_text}
"""
    client_options = {}

    client = create_gemini_client()

    response = client.models.generate_content(
        model=Config.GEMINI_EXTRACT_MODEL,
        contents=prompt,
    )
    if not response.text:
        raise RuntimeError("Gemini không trả về nội dung")

    cleaned = response.text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json"):]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return json.loads(cleaned.strip())


def load_matching_resources(progress_callback) -> tuple[list[dict], dict]:
    global INVESTORS, INVESTOR_EMBEDDINGS
    if INVESTORS is not None and INVESTOR_EMBEDDINGS is not None:
        return INVESTORS, INVESTOR_EMBEDDINGS

    with RESOURCE_LOCK:
        if INVESTORS is None or INVESTOR_EMBEDDINGS is None:
            progress_callback(42, "Đang tải mô hình embedding lần đầu...")
            from pipeline import precompute_investor_embeddings

            with (Config.BASE_DIR / "investors_data.json").open("r", encoding="utf-8") as handle:
                investors = json.load(handle)
            embeddings = precompute_investor_embeddings(investors)
            INVESTORS = investors
            INVESTOR_EMBEDDINGS = embeddings

    return INVESTORS, INVESTOR_EMBEDDINGS


def run_analysis_job(job_id: str, pdf_path: Path) -> None:
    def progress(percent: int, message: str) -> None:
        set_job(job_id, status="running", progress=percent, message=message)

    try:
        progress(5, "Đang đọc nội dung PDF...")
        raw_text = process_pitchdeck(pdf_path)
        if not raw_text.strip():
            raise ValueError("Không trích xuất được văn bản từ PDF")

        progress(22, "Gemini đang bóc tách dữ liệu startup...")
        startup_data = extract_startup_with_gemini(raw_text)
        startup = startup_data[0] if isinstance(startup_data, list) else startup_data
        if not isinstance(startup, dict):
            raise ValueError("Dữ liệu startup trả về không đúng định dạng")

        investors, investor_embeddings = load_matching_resources(progress)

        progress(55, "Đang lọc quỹ theo ngành, vòng vốn và ticket size...")
        from pipeline import convert_match, hard_filter, semantic_match

        filtered = hard_filter(startup, investors)
        if not filtered:
            set_job(
                job_id,
                status="completed",
                progress=100,
                message="Không tìm thấy quỹ thỏa điều kiện lọc cứng",
                result=[],
                finished_timestamp=time.time(),
            )
            return

        progress(65, "Đang tính điểm tương đồng ngữ nghĩa...")
        matches = semantic_match(startup, filtered, investor_embeddings)[: Config.TOP_MATCHES]

        final_results = []
        total = max(1, len(matches))
        for index, match in enumerate(matches, start=1):
            percent = 68 + int((index - 1) / total * 27)
            progress(percent, f"Đang tạo phân tích và email cho quỹ {index}/{total}...")
            final_results.append(convert_match(match, startup))

        set_job(
            job_id,
            status="completed",
            progress=100,
            message="Hoàn tất phân tích",
            result=final_results,
            finished_timestamp=time.time(),
        )
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        set_job(
            job_id,
            status="failed",
            progress=100,
            message="Phân tích thất bại",
            error=str(exc),
            finished_timestamp=time.time(),
        )
    finally:
        try:
            pdf_path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Không xóa được file tạm %s", pdf_path)


@app.post("/api/analyze")
def start_analysis():
    cleanup_old_jobs()

    if not Config.GEMINI_API_KEY:
        return jsonify({"error": "Backend chưa cấu hình GEMINI_API_KEY"}), 503

    if not rate_limit_allows(client_ip()):
        return jsonify({"error": "Bạn gửi quá nhiều yêu cầu. Vui lòng thử lại sau."}), 429

    if active_job_count() >= Config.MAX_QUEUED_JOBS:
        return jsonify({"error": "Máy chủ đang bận. Hàng đợi demo đã đầy."}), 429

    uploaded = request.files.get("pdf_file")
    if uploaded is None or not uploaded.filename:
        return jsonify({"error": "Không tìm thấy file PDF"}), 400

    if not uploaded.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Chỉ chấp nhận file PDF"}), 400

    signature = uploaded.stream.read(5)
    uploaded.stream.seek(0)
    if signature != b"%PDF-":
        return jsonify({"error": "Nội dung file không phải PDF hợp lệ"}), 400

    with tempfile.NamedTemporaryFile(
        mode="wb",
        suffix=".pdf",
        prefix="upload_",
        dir=UPLOAD_DIR,
        delete=False,
    ) as temp_file:
        shutil.copyfileobj(uploaded.stream, temp_file)
        pdf_path = Path(temp_file.name)

    job_id = uuid.uuid4().hex
    with JOBS_LOCK:
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "message": "Đã đưa vào hàng đợi",
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }

    EXECUTOR.submit(run_analysis_job, job_id, pdf_path)
    return jsonify({"job_id": job_id, "status": "queued"}), 202


@app.get("/api/jobs/<job_id>")
def get_job(job_id: str):
    cleanup_old_jobs()
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if job is None:
            return jsonify({"error": "Không tìm thấy tác vụ"}), 404
        public_job = {key: value for key, value in job.items() if key != "finished_timestamp"}
    return jsonify(public_job)
