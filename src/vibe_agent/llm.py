import json
import os
from dotenv import load_dotenv, find_dotenv
from google import genai
from google.genai import types

load_dotenv(find_dotenv(usecwd=True))   # read .env so os.getenv can find GEMINI_API_KEY

MODEL = "gemini-3.6-flash"
LLM_TIMEOUT_MS = 120_000   # free tier is slow; drop to ~20_000 on a paid plan


def ask_llm(prompt: str) -> dict:
    # connect to Gemini with the key from .env, and give up if it takes too long
    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY"),
        http_options=types.HttpOptions(timeout=LLM_TIMEOUT_MS),
    )

    # send the prompt, wait for the reply
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0,
            thinking_config=types.ThinkingConfig(thinking_level="low"),   # simple question: don't overthink
        ),
    )

    # turn the reply text into a Python dict
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {}