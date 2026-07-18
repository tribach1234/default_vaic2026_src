from google import genai
from google.genai import types

from config import Config


def create_gemini_client():
    if not Config.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured in local-backend/.env"
        )

    client_options = {}

    if Config.GEMINI_BASE_URL:
        client_options["http_options"] = types.HttpOptions(
            base_url=Config.GEMINI_BASE_URL
        )

    return genai.Client(
        api_key=Config.GEMINI_API_KEY,
        **client_options
    )