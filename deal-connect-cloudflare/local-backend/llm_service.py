from google import genai
from google.genai import types
from gemini_client import create_gemini_client
from config import Config
from prompts import get_email_prompt, get_match_reason_prompt

_client = None



def _get_client():
    global _client

    if _client is None:
        _client = create_gemini_client()

    return _client


def generate_email_content(startup: dict, investor: dict, match_score: float, match_reason: str) -> str:
    prompt_text = get_email_prompt(startup, investor, match_score, match_reason)
    response = _get_client().models.generate_content(
        model=Config.GEMINI_TEXT_MODEL,
        contents=prompt_text,
    )
    return response.text.strip() if response.text else ""


def generate_match_reason(startup: dict, investor: dict) -> str:
    prompt_text = get_match_reason_prompt(startup, investor)
    response = _get_client().models.generate_content(
        model=Config.GEMINI_TEXT_MODEL,
        contents=prompt_text,
    )
    return response.text.strip() if response.text else ""
