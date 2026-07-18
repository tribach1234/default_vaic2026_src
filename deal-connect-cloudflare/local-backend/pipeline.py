from filter_and_semantic_matching import (
    hard_filter,
    precompute_investor_embeddings,
    semantic_match,
)
from llm_service import generate_email_content, generate_match_reason


def reason_generate(startup: dict, investor: dict) -> str:
    return generate_match_reason(startup, investor)


def convert_match(match_result: dict, startup: dict) -> dict:
    scores = {}
    for score_line in match_result["indiv_score"]:
        key, value = score_line.split(" matching score: ", maxsplit=1)
        scores[key] = float(value)

    startup_info = {
        "name": startup.get("name", ""),
        "industry": startup.get("industry", ""),
        "technology": scores.get("technology_focus", 0),
        "problem": scores.get("problem_focus", 0),
        "investment_thesis": scores.get("investment_thesis", 0),
        "customers": scores.get("customer_focus", 0),
    }

    investor_info = {
        "id": match_result["id"],
        "name": match_result["name"],
        "target_industries": match_result.get("target_industries", ["Đa ngành"]),
    }

    match_reason = reason_generate(startup_info, investor_info)
    return {
        "startup": startup_info,
        "investor": investor_info,
        "match_score": match_result["score"],
        "match_reason": match_reason,
        "generated_email": generate_email_content(
            startup_info,
            investor_info,
            match_result["score"],
            match_reason,
        ),
    }
