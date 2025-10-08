import os

class FLAGS:
    ENABLE_LLM: bool = os.getenv("UR_ENABLE_LLM", "0") == "1"
    MODEL: str = os.getenv("UR_LLM_MODEL", "gpt-4o-mini")
    MAX_TOKENS: int = int(os.getenv("UR_LLM_MAX_TOKENS", "400"))
