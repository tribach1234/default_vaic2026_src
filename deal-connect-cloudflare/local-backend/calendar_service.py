# calendar_service.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable


TimeInterval = tuple[datetime, datetime]


def _normalize_intervals(intervals: Iterable[TimeInterval]) -> list[TimeInterval]:
    normalized: list[TimeInterval] = []

    for start_time, end_time in intervals:
        if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
            raise TypeError("Calendar intervals must contain datetime objects")
        if start_time >= end_time:
            continue
        normalized.append((start_time, end_time))

    return sorted(normalized, key=lambda interval: interval[0])


def find_common_free_intervals(
    investor_free: Iterable[TimeInterval],
    startup_free: Iterable[TimeInterval],
) -> list[TimeInterval]:
    investor_intervals = _normalize_intervals(investor_free)
    startup_intervals = _normalize_intervals(startup_free)

    if not startup_intervals:
        return investor_intervals
    if not investor_intervals:
        return []

    common: list[TimeInterval] = []
    investor_index = 0
    startup_index = 0

    while (
        investor_index < len(investor_intervals)
        and startup_index < len(startup_intervals)
    ):
        investor_start, investor_end = investor_intervals[investor_index]
        startup_start, startup_end = startup_intervals[startup_index]

        common_start = max(investor_start, startup_start)
        common_end = min(investor_end, startup_end)

        if common_start < common_end:
            common.append((common_start, common_end))

        if investor_end <= startup_end:
            investor_index += 1
        else:
            startup_index += 1

    return common


def find_all_common_free_slots(
    investor_free: Iterable[TimeInterval],
    startup_free: Iterable[TimeInterval],
    duration_minutes: int = 60,
    step_minutes: int = 30,
) -> list[TimeInterval]:
    if duration_minutes <= 0:
        raise ValueError("duration_minutes must be greater than zero")
    if step_minutes <= 0:
        raise ValueError("step_minutes must be greater than zero")

    duration = timedelta(minutes=duration_minutes)
    step = timedelta(minutes=step_minutes)
    slots: list[TimeInterval] = []

    for free_start, free_end in find_common_free_intervals(
        investor_free,
        startup_free,
    ):
        current_start = free_start
        while current_start + duration <= free_end:
            slots.append((current_start, current_start + duration))
            current_start += step

    return slots


def serialize_slot(start_time: datetime, end_time: datetime) -> dict:
    return {
        "start_time_iso": start_time.isoformat(),
        "end_time_iso": end_time.isoformat(),
        "date": start_time.strftime("%d/%m/%Y"),
        "start_time": start_time.strftime("%H:%M"),
        "end_time": end_time.strftime("%H:%M"),
        "label": (
            f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}, "
            f"{start_time.strftime('%d/%m/%Y')}"
        ),
    }
