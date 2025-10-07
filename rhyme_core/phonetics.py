# Minimal placeholders; replace with real logic when ready.
import re

VOWELS = {""AA"",""AE"",""AH"",""AO"",""AW"",""AY"",""EH"",""ER"",""EY"",""IH"",""IY"",""OW"",""OY"",""UH"",""UW""}

def stress_pattern(pron_arpabet: str) -> str:
    # naive extraction of 0/1/2 from digits in phones like 'AE1'
    digs = [c for c in pron_arpabet if c.isdigit()]
    return """" .join(digs) if digs else """"

def k_keys(phones: list[str]) -> tuple[str,str,str]:
    # crude: last stressed vowel as k1; nucleus+coda as k2; tail as k3
    tail = []
    k1 = """"
    last_stressed_idx = -1
    for i, p in enumerate(phones):
        if any(v in p for v in VOWELS) and any(d in p for d in ""12""):
            last_stressed_idx = i
    if last_stressed_idx >= 0:
        k1 = re.sub(r""\d"", """", phones[last_stressed_idx])
        tail = [re.sub(r""\d"", """", t) for t in phones[last_stressed_idx:]]
    k2 = ""-"" .join(tail[:2]) if tail else """"
    k3 = ""-"" .join(tail)
    return k1, k2, k3
