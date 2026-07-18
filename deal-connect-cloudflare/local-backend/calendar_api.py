# calendar_api.py
from __future__ import annotations

from flask import Blueprint, jsonify, request

from calendar_path import confirm_mock_schedule, get_mock_available_slots


calendar_bp = Blueprint("calendar_api", __name__)


@calendar_bp.post("/api/calendar/schedule")
def get_investor_available_slots():
    """
    Trả về các khoảng thời gian rảnh chung từ dữ liệu lịch mock.
    Endpoint này không tự động chọn hoặc xác nhận lịch.
    """
    payload = request.get_json(silent=True) or {}
    investor = payload.get("investor")

    if not isinstance(investor, dict):
        return jsonify({
            "error": "Trường 'investor' là bắt buộc và phải là một object."
        }), 400

    try:
        result = get_mock_available_slots(investor)

        if not result["available_slots"]:
            return jsonify({
                **result,
                "message": "Không tìm thấy khoảng thời gian rảnh chung phù hợp."
            }), 200

        return jsonify(result), 200
    except Exception as exc:
        return jsonify({
            "error": f"Không thể tìm khoảng thời gian phù hợp: {exc}"
        }), 500


@calendar_bp.post("/api/calendar/confirm")
def confirm_startup_selected_slot():
    """
    Xác nhận khung giờ mà startup đã chủ động lựa chọn.

    Payload:
    {
      "investor": {...},
      "selected_slot": {
        "start_time_iso": "...",
        "end_time_iso": "..."
      }
    }
    """
    payload = request.get_json(silent=True) or {}
    investor = payload.get("investor")
    selected_slot = payload.get("selected_slot")

    if not isinstance(investor, dict):
        return jsonify({
            "error": "Trường 'investor' là bắt buộc và phải là một object."
        }), 400

    if not isinstance(selected_slot, dict):
        return jsonify({
            "error": "Trường 'selected_slot' là bắt buộc và phải là một object."
        }), 400

    try:
        result = confirm_mock_schedule(
            investor=investor,
            selected_slot=selected_slot,
        )
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({
            "error": f"Không thể xác nhận lịch đã chọn: {exc}"
        }), 500


def register_calendar_routes(app) -> None:
    if "calendar_api" not in app.blueprints:
        app.register_blueprint(calendar_bp)
