# llm_service.py
from __future__ import annotations

import json
import re
from typing import Any

from config import Config
from gemini_client import create_gemini_client
from prompts import (
    get_email_prompt,
    get_match_reason_prompt,
    get_mock_startup_reply_prompt,
    get_time_extraction_prompt,
)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = create_gemini_client()
    return _client


def _generate_text(prompt_text: str) -> str:
    response = _get_client().models.generate_content(
        model=Config.GEMINI_TEXT_MODEL,
        contents=prompt_text,
    )
    return (response.text or "").strip()


def generate_email_content(
    startup: dict,
    investor: dict,
    match_score: float,
    match_reason: str,
) -> str:
    return _generate_text(
        get_email_prompt(startup, investor, match_score, match_reason)
    )


def generate_match_reason(startup: dict, investor: dict) -> str:
    return _generate_text(get_match_reason_prompt(startup, investor))


def _extract_json_object(text: str) -> dict[str, Any]:
    cleaned = (
        (text or "")
        .replace("```json", "")
        .replace("```JSON", "")
        .replace("```", "")
        .strip()
    )

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(0))

    if not isinstance(parsed, dict):
        raise ValueError("Gemini response must be a JSON object")
    return parsed


def generate_mock_startup_reply(
    start_time,
    end_time,
    investor_name: str = "quỹ đầu tư",
) -> str:
    start_str = start_time.strftime("%H:%M")
    end_str = end_time.strftime("%H:%M")
    date_str = start_time.strftime("%d/%m/%Y")

    prompt_text = get_mock_startup_reply_prompt(
        start_str,
        end_str,
        date_str,
        investor_name=investor_name,
    )

    try:
        reply = _generate_text(prompt_text)
        if reply:
            return reply
    except Exception as exc:
        print(f"Lỗi khi tạo mock startup reply: {exc}")

    return (
        f"Chúng tôi xác nhận lịch họp với {investor_name} từ "
        f"{start_str} đến {end_str} ngày {date_str} (giờ Việt Nam)."
    )


def extract_chosen_time(reply_text: str) -> dict | None:
    try:
        time_data = _extract_json_object(
            _generate_text(get_time_extraction_prompt(reply_text))
        )

        start_time_iso = str(time_data.get("start_time_iso", "")).strip()
        end_time_iso = str(time_data.get("end_time_iso", "")).strip()

        if not start_time_iso or not end_time_iso:
            raise ValueError("Missing start_time_iso or end_time_iso")

        return {
            "start_time_iso": start_time_iso,
            "end_time_iso": end_time_iso,
        }
    except Exception as exc:
        print(f"Lỗi khi bóc tách thời gian: {exc}")
        return None
