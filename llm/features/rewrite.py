from ..providers import chat
from config import FLAGS

SYSTEM = "You rewrite a single line to end with a specified rhyme tail and keep similar meaning/tone."

def rewrite_with_scheme(line: str, rhyme_tail: str, style: str = "neutral") -> str:
    if not FLAGS.ENABLE_LLM:
        return "LLM disabled."
    user = (
        f"Rewrite the line to end with '{rhyme_tail}'. Keep meaning, keep length-ish, style={style}.\n"
        f"Line: {line}"
    )
    return chat(
        [{"role":"system","content":SYSTEM},{"role":"user","content":user}],
        model=FLAGS.MODEL,
        max_tokens=FLAGS.MAX_TOKENS,
    )
