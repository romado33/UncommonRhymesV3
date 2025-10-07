from pathlib import Path
import gradio as gr
from rhyme_core.search import search_all_categories
from rhyme_core.data.paths import rap_db as get_rap_db

def go(term, max_items, relax_rap):
    res = search_all_categories(term, max_items=max_items, relax_rap=relax_rap)
    ui = {}
    for k in ["uncommon","slant","multiword","rap_targets"]:
        items = res.get(k, [])
        total = res.get(k+"_total", len(items))
        ui[k] = [f"{r['word'] if 'word' in r else r.get('target_word','?')} â€” {r.get('why','')}" for r in items]
        if total > len(items):
            ui[k].append(f"... See all ({total})")
    return ui["uncommon"], ui["slant"], ui["multiword"], ui["rap_targets"]

with gr.Blocks() as demo:
    gr.Markdown("# UncommonRhymesV3")
    term = gr.Textbox(label="Word or phrase")
    max_items = gr.Slider(5, 50, value=20, step=1, label="Max per category (display)")
    relax_rap = gr.Checkbox(value=True, label="Relax rap matching (include assonance/slant top-up)")
    btn = gr.Button("Analyze")
    uncommon = gr.HighlightedText(label="Uncommon", combine_adjacent=True)
    slant    = gr.HighlightedText(label="Slant", combine_adjacent=True)
    multi    = gr.HighlightedText(label="Multiword", combine_adjacent=True)
    rap      = gr.HighlightedText(label="Rap Targets", combine_adjacent=True)

    btn.click(go, inputs=[term, max_items, relax_rap], outputs=[uncommon, slant, multi, rap])

if __name__ == "__main__":
    demo.launch()
