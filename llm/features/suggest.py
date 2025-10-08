from typing import Sequence
from ..providers import chat
from config import FLAGS

SYSTEM = "You are a creative rap writing assistant. Suggest clever targets that fit the rhyme tail; 1-line ideas."

def suggest_targets(query: str, rhyme_tail: str, bucket: str, examples: Sequence[str]) -> str:
    if not FLAGS.ENABLE_LLM:
        return "LLM disabled."
    user = (
        f"Query='{query}', tail='{rhyme_tail}', bucket='{bucket}'. "
        f"Given these candidates:\n- " + "\n- ".join(examples[:20]) +
        "\nSuggest 8 punchy target ideas (just the target phrase; no explanation)."
    )
    return chat(
        [{"role":"system","content":SYSTEM},{"role":"user","content":user}],
        model=FLAGS.MODEL,
        max_tokens=FLAGS.MAX_TOKENS,
    )
