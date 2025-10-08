param(
  [string]$RepoPath = "."
)

function Write-File($Path, $Content) {
  $dir = Split-Path $Path
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $Content | Out-File -FilePath $Path -Encoding UTF8 -Force
}

$root = Resolve-Path $RepoPath
if (-not (Test-Path (Join-Path $root "app.py"))) {
  Write-Error "app.py not found. Run this from the UncommonRhymesV3 repo root or pass -RepoPath."
  exit 1
}

# 1) requirements.txt — ensure openai present
$reqPath = Join-Path $root "requirements.txt"
if (-not (Test-Path $reqPath)) { New-Item -ItemType File -Path $reqPath | Out-Null }
$req = Get-Content $reqPath -Raw
if ($req -notmatch "(?m)^\s*openai\s*>=") {
  Add-Content $reqPath "`nopenai>=1.52.0"
  Write-Host "✅ Added openai to requirements.txt"
} else {
  Write-Host "ℹ️  openai already present in requirements.txt"
}

# 2) config.py
$config = @"
import os

class FLAGS:
    ENABLE_LLM: bool = os.getenv("UR_ENABLE_LLM", "0") == "1"
    MODEL: str = os.getenv("UR_LLM_MODEL", "gpt-4o-mini")
    MAX_TOKENS: int = int(os.getenv("UR_LLM_MAX_TOKENS", "400"))
"@
Write-File (Join-Path $root "config.py") $config

# 3) llm/providers.py
$providers = @"
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
"@
Write-File (Join-Path $root "llm\providers.py") $providers

# 4) llm/features/*
$init_llm = @"
from .providers import get_client
"@
Write-File (Join-Path $root "llm\__init__.py") $init_llm

$explain = @"
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
"@
$suggest = @"
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
"@
$rewrite = @"
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
"@

Write-File (Join-Path $root "llm\features\__init__.py") ""
Write-File (Join-Path $root "llm\features\explain.py") $explain
Write-File (Join-Path $root "llm\features\suggest.py") $suggest
Write-File (Join-Path $root "llm\features\rewrite.py") $rewrite

# 5) patch app.py (replace with LLM-enabled UI)
$appPath = Join-Path $root "app.py"
$appNew = @"
from pathlib import Path
import gradio as gr
from rhyme_core.search import search_all_categories
from config import FLAGS
from llm.features.explain import explain_rhyme
from llm.features.suggest import suggest_targets
from llm.features.rewrite import rewrite_with_scheme

def go(term, max_items, relax_rap, do_explain, do_suggest, do_rewrite, rewrite_line, rewrite_tail):
    term = (term or '').strip()
    if not term:
        return [], [], [], [], 'Enter a term above.', '', ''
    res = search_all_categories(term, max_items=max_items, relax_rap=relax_rap)

    def to_list(bucket):
        items = res.get(bucket, [])
        total = res.get(bucket + '_total', len(items))
        rows = [f""{(r.get('word') or r.get('target_word') or '?')} — {r.get('why','')}"" for r in items]
        if total > len(items):
            rows.append(f""... See all ({total})"")
        return rows

    uncommon = to_list('uncommon')
    slant    = to_list('slant')
    multi    = to_list('multiword')
    rap      = to_list('rap_targets')

    llm_explain = llm_suggest = llm_rewrite = ''
    if FLAGS.ENABLE_LLM:
        if do_explain:
            llm_explain = explain_rhyme(term, phones='', candidates=res.get('uncommon', []))
        if do_suggest:
            sample = [(r.get('word') or r.get('target_word') or '') for r in (res.get('slant', []) + res.get('uncommon', []))]
            llm_suggest = suggest_targets(term, rhyme_tail='(auto)', bucket='mixed', examples=sample)
        if do_rewrite and rewrite_line and rewrite_tail:
            llm_rewrite = rewrite_with_scheme(rewrite_line, rewrite_tail)
    else:
        note = 'LLM disabled. Set UR_ENABLE_LLM=1 and OPENAI_API_KEY.'
        llm_explain = llm_suggest = llm_rewrite = note

    return uncommon, slant, multi, rap, llm_explain, llm_suggest, llm_rewrite

with gr.Blocks() as demo:
    gr.Markdown('# UncommonRhymesV3')
    with gr.Row():
        term = gr.Textbox(label='Word or phrase', scale=3)
        max_items = gr.Slider(5, 50, value=20, step=1, label='Max per category')
        relax_rap = gr.Checkbox(value=True, label='Relax rap matching')
    btn = gr.Button('Analyze')

    uncommon = gr.HighlightedText(label='Uncommon', combine_adjacent=True)
    slant    = gr.HighlightedText(label='Slant', combine_adjacent=True)
    multi    = gr.HighlightedText(label='Multiword', combine_adjacent=True)
    rap      = gr.HighlightedText(label='Rap Targets', combine_adjacent=True)

    with gr.Accordion('LLM helpers (optional)', open=False):
        do_explain = gr.Checkbox(label='Explain top matches', value=False)
        do_suggest = gr.Checkbox(label='Suggest punchline targets', value=False)
        do_rewrite = gr.Checkbox(label='Rewrite a line to rhyme', value=False)
        rewrite_line = gr.Textbox(label='Line to rewrite')
        rewrite_tail = gr.Textbox(label='Target tail (e.g., UH-BL / double)')
        llm_explain = gr.Markdown()
        llm_suggest = gr.Markdown()
        llm_rewrite = gr.Markdown()

    btn.click(
        go,
        inputs=[term, max_items, relax_rap, do_explain, do_suggest, do_rewrite, rewrite_line, rewrite_tail],
        outputs=[uncommon, slant, multi, rap, llm_explain, llm_suggest, llm_rewrite]
    )

if __name__ == '__main__':
    demo.launch()
"@
Write-File $appPath $appNew

# 6) test_llm_smoke.py (skips when no key/flag)
$testLLM = @"
import os, pytest
from config import FLAGS
from llm.features.rewrite import rewrite_with_scheme

@pytest.mark.skipif(not FLAGS.ENABLE_LLM or not os.getenv('OPENAI_API_KEY'), reason='LLM disabled')
def test_rewrite_smoke():
    out = rewrite_with_scheme('Keep it humble', 'double')
    assert isinstance(out, str) and len(out) > 0
"@
Write-File (Join-Path $root "tests\test_llm_smoke.py") $testLLM

# 7) add UR_ENABLE_LLM to scripts/set-env.ps1 if present
$setEnv = Join-Path $root "scripts\set-env.ps1"
if (Test-Path $setEnv) {
  $txt = Get-Content $setEnv -Raw
  if ($txt -notmatch "UR_ENABLE_LLM") {
    Add-Content $setEnv "`$env:UR_ENABLE_LLM = '1'"
    Write-Host "✅ Added UR_ENABLE_LLM=1 to scripts/set-env.ps1"
  } else {
    Write-Host "ℹ️  UR_ENABLE_LLM already present in set-env.ps1"
  }
}

Write-Host "`n✅ LLM pack installed. Next steps:"
Write-Host "1) Set env:  .\scripts\set-env.ps1   (and set OPENAI_API_KEY)"
Write-Host "2) Install deps:  pip install -r requirements.txt"
Write-Host "3) Run app:  python app.py"
