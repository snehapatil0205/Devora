import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = (os.getenv("GROQ_API_KEY") or "").strip()
MODEL = (os.getenv("GROQ_MODEL") or "openai/gpt-oss-120b").strip()

if not API_KEY:
    raise RuntimeError("GROQ_API_KEY is missing from environment or .env file.")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


def ask_llm(instructions: str, input_text: str) -> str:
    """Send a direct completion request without tools."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": input_text},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""