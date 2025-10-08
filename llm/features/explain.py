from typing import Sequence
from ..providers import chat
from config import FLAGS

SYSTEM = "You are a concise rap rhyme analyst. Explain why items rhyme using ARPAbet, stress, and coda."

def explain_rhyme(query: str, phones: str, candidates: Sequence[dict]) -> str:
    if not FLAGS.ENABLE_LLM:
        return "LLM disabled."
    top = candidates[:10]
    lines = [f"- {c.get('word') or c.get('target_word','?')}: {c.get('why','')} (pron: {c.get('pron','?')})" for c in top]
    user = (
        f"Query: {query}\nQuery phones: {phones}\n"
        "Explain (bullet points) why these rhyme/near-rhyme, referencing stressed vowel & coda:\n"
        + "\n".join(lines)
    )
    return chat(
        [{"role":"system","content":SYSTEM},{"role":"user","content":user}],
        model=FLAGS.MODEL,
        max_tokens=FLAGS.MAX_TOKENS,
    )
