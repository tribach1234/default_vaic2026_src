import os
import re
import threading
from typing import Any

from sentence_transformers import SentenceTransformer, util

from config import Config

FIELD_MAPPING = [
    ("technology", "technology_focus", 0.35),
    ("problem", "problem_focus", 0.25),
    ("solution", "investment_thesis", 0.25),
    ("customers", "customer_focus", 0.15),
]

_model = None
_model_lock = threading.Lock()


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = SentenceTransformer(Config.EMBEDDING_MODEL)
    return _model


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def embed_text(text: Any):
    return _get_model().encode(_text(text), normalize_embeddings=True)


def precompute_investor_embeddings(investors: list[dict]) -> dict:
    investor_cache = {}
    for investor in investors:
        investor_cache[investor["id"]] = {
            "name": investor["name"],
            "embeddings": {
                investor_field: embed_text(investor.get(investor_field, ""))
                for _, investor_field, _ in FIELD_MAPPING
            },
        }
    return investor_cache


def parse_ticket_size(ticket_size: str) -> tuple[int, int]:
    minimum, maximum = ticket_size.split("-", maxsplit=1)
    return int(minimum.strip()), int(maximum.strip())


def parse_funding(value: Any) -> int:
    if isinstance(value, (int, float)):
        return int(value)

    text = str(value or "").strip().lower().replace(",", "")
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([kmb]?)", text)
    if not match:
        raise ValueError("Không xác định được số tiền gọi vốn từ Pitch Deck")

    amount = float(match.group(1))
    multiplier = {"": 1, "k": 1_000, "m": 1_000_000, "b": 1_000_000_000}[match.group(2)]
    return int(amount * multiplier)


def _normalized(value: Any) -> str:
    return re.sub(r"\s+", " ", _text(value).strip().casefold())


def hard_filter(startup: dict, investors: list[dict]) -> list[dict]:
    candidates = []
    startup_industry = _normalized(startup.get("industry"))
    startup_stage = _normalized(startup.get("stage"))
    funding = parse_funding(startup.get("funding"))

    for investor in investors:
        industries = [_normalized(item) for item in investor.get("target_industries", [])]
        stages = [_normalized(item) for item in investor.get("target_stages", [])]

        # Chấp nhận cả khớp chính xác và một chuỗi chứa chuỗi còn lại.
        industry_match = any(
            startup_industry == item or startup_industry in item or item in startup_industry
            for item in industries
            if item and startup_industry
        )
        if not industry_match:
            continue

        if startup_stage not in stages:
            continue

        min_ticket, max_ticket = parse_ticket_size(investor["ticket_size"])
        if not (min_ticket <= funding <= max_ticket):
            continue

        candidates.append(investor)

    return candidates


def semantic_match(startup: dict, candidate_investors: list[dict], investor_cache: dict) -> list[dict]:
    startup_embeddings = {
        startup_field: embed_text(startup.get(startup_field, ""))
        for startup_field, _, _ in FIELD_MAPPING
    }

    results = []
    for investor in candidate_investors:
        investor_id = investor["id"]
        total_score = 0.0
        indiv_score = []

        for startup_field, investor_field, weight in FIELD_MAPPING:
            similarity = util.cos_sim(
                startup_embeddings[startup_field],
                investor_cache[investor_id]["embeddings"][investor_field],
            ).item()
            indiv_score.append(f"{investor_field} matching score: {similarity}")
            total_score += similarity * weight

        results.append(
            {
                "id": investor["id"],
                "name": investor["name"],
                "target_industries": investor.get("target_industries", []),
                "score": round(total_score, 4),
                "indiv_score": indiv_score,
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)
    return results
