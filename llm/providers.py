import os
from typing import List, Dict
from openai import OpenAI

_client = None

def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _client

def chat(messages: List[Dict[str, str]], model: str, max_tokens: int = 400) -> str:
    client = get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return resp.choices[0].message.content or ""
