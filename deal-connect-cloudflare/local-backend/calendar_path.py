# calendar_path.py
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from calendar_service import find_all_common_free_slots, serialize_slot


VIETNAM_TZ = timezone(timedelta(hours=7))
MEETING_DURATION_MINUTES = 60
MAX_SUGGESTED_SLOTS = 6

# Dữ liệu lịch mock dùng cho demo hackathon.
INVESTOR_FREE_INTERVALS = [
    (datetime(2026, 7, 20, 9, 0, tzinfo=VIETNAM_TZ), datetime(2026, 7, 20, 11, 0, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 20, 14, 0, tzinfo=VIETNAM_TZ), datetime(2026, 7, 20, 16, 0, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 21, 10, 0, tzinfo=VIETNAM_TZ), datetime(2026, 7, 21, 12, 0, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 21, 15, 0, tzinfo=VIETNAM_TZ), datetime(2026, 7, 21, 17, 0, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 22, 8, 30, tzinfo=VIETNAM_TZ), datetime(2026, 7, 22, 10, 30, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 22, 13, 30, tzinfo=VIETNAM_TZ), datetime(2026, 7, 22, 15, 30, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 23, 9, 30, tzinfo=VIETNAM_TZ), datetime(2026, 7, 23, 11, 30, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 23, 16, 0, tzinfo=VIETNAM_TZ), datetime(2026, 7, 23, 18, 0, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 24, 10, 0, tzinfo=VIETNAM_TZ), datetime(2026, 7, 24, 12, 0, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 24, 14, 30, tzinfo=VIETNAM_TZ), datetime(2026, 7, 24, 16, 30, tzinfo=VIETNAM_TZ)),
]

STARTUP_FREE_INTERVALS = [
    (datetime(2026, 7, 20, 10, 0, tzinfo=VIETNAM_TZ), datetime(2026, 7, 20, 12, 0, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 20, 13, 0, tzinfo=VIETNAM_TZ), datetime(2026, 7, 20, 15, 0, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 21, 8, 0, tzinfo=VIETNAM_TZ), datetime(2026, 7, 21, 10, 30, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 21, 16, 0, tzinfo=VIETNAM_TZ), datetime(2026, 7, 21, 18, 0, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 22, 9, 0, tzinfo=VIETNAM_TZ), datetime(2026, 7, 22, 11, 0, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 22, 14, 0, tzinfo=VIETNAM_TZ), datetime(2026, 7, 22, 17, 0, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 23, 8, 0, tzinfo=VIETNAM_TZ), datetime(2026, 7, 23, 9, 30, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 23, 15, 0, tzinfo=VIETNAM_TZ), datetime(2026, 7, 23, 17, 0, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 24, 11, 0, tzinfo=VIETNAM_TZ), datetime(2026, 7, 24, 13, 0, tzinfo=VIETNAM_TZ)),
    (datetime(2026, 7, 24, 15, 0, tzinfo=VIETNAM_TZ), datetime(2026, 7, 24, 16, 0, tzinfo=VIETNAM_TZ)),
]


def get_mock_available_slots(
    investor: dict[str, Any],
    duration_minutes: int = MEETING_DURATION_MINUTES,
    max_suggestions: int = MAX_SUGGESTED_SLOTS,
) -> dict[str, Any]:
    """Tìm và trả về các khoảng thời gian rảnh chung từ dữ liệu mock."""
    investor_name = str(investor.get("name") or "Nhà đầu tư chưa xác định")
    investor_id = investor.get("id")

    all_slots = find_all_common_free_slots(
        INVESTOR_FREE_INTERVALS,
        STARTUP_FREE_INTERVALS,
        duration_minutes=duration_minutes,
        step_minutes=30,
    )

    available_slots = [
        serialize_slot(start_time, end_time)
        for start_time, end_time in all_slots[:max_suggestions]
    ]

    return {
        "status": "available",
        "source": "mock_calendar_data",
        "timezone": "Asia/Ho_Chi_Minh",
        "duration_minutes": duration_minutes,
        "investor": {
            "id": investor_id,
            "name": investor_name,
        },
        "total_available_slots": len(available_slots),
        "available_slots": available_slots,
    }


def confirm_mock_schedule(
    investor: dict[str, Any],
    selected_slot: dict[str, Any],
    duration_minutes: int = MEETING_DURATION_MINUTES,
    max_suggestions: int = MAX_SUGGESTED_SLOTS,
) -> dict[str, Any]:
    """
    Xác nhận một khung giờ do startup lựa chọn.

    Chỉ chấp nhận slot có trong danh sách rảnh chung hiện tại.
    Không chọn random và không gọi Gemini.
    """
    if not isinstance(selected_slot, dict):
        raise ValueError("selected_slot phải là một object")

    selected_start = str(selected_slot.get("start_time_iso") or "").strip()
    selected_end = str(selected_slot.get("end_time_iso") or "").strip()

    if not selected_start or not selected_end:
        raise ValueError(
            "selected_slot phải có start_time_iso và end_time_iso"
        )

    availability = get_mock_available_slots(
        investor=investor,
        duration_minutes=duration_minutes,
        max_suggestions=max_suggestions,
    )

    valid_slot = next(
        (
            slot
            for slot in availability["available_slots"]
            if slot["start_time_iso"] == selected_start
            and slot["end_time_iso"] == selected_end
        ),
        None,
    )

    if valid_slot is None:
        raise ValueError(
            "Khung giờ đã chọn không nằm trong danh sách thời gian phù hợp"
        )

    return {
        "status": "confirmed",
        "source": "mock_calendar_data",
        "booking_id": uuid.uuid4().hex,
        "confirmed_at": datetime.now(VIETNAM_TZ).isoformat(),
        "timezone": availability["timezone"],
        "duration_minutes": availability["duration_minutes"],
        "investor": availability["investor"],
        "selected_slot": valid_slot,
        "message": "Startup đã xác nhận khung giờ phù hợp.",
    }


# Giữ alias cũ để tránh lỗi import ở các phần chưa cập nhật.
def create_mock_schedule(
    investor: dict[str, Any],
    duration_minutes: int = MEETING_DURATION_MINUTES,
    max_suggestions: int = MAX_SUGGESTED_SLOTS,
) -> dict[str, Any]:
    return get_mock_available_slots(
        investor=investor,
        duration_minutes=duration_minutes,
        max_suggestions=max_suggestions,
    )
