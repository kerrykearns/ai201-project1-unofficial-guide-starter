"""
app.py — Milestone 5: Gradio Web Interface
The Unofficial Guide — CS Professor Reviews at University of Delaware

Pipeline stage: Generation → [Gradio UI] → User

Run with:
    python app.py

Then open the URL printed in the terminal (typically http://127.0.0.1:7860).

Requires:
    pip install gradio
    (query.py, retrieve.py, embed.py, ingest.py and chroma_db/ must all be
     present and embed.py must have been run at least once)
"""

import gradio as gr
from query import ask

# ---------------------------------------------------------------------------
# HANDLER
# ---------------------------------------------------------------------------


def handle_query(question: str):
    """
    Called by Gradio whenever the user clicks Ask or presses Enter.

    Returns a tuple (answer_text, sources_text) mapped to the two output
    textboxes.  Empty or whitespace-only questions are rejected immediately
    without touching the API.
    """
    if not question or not question.strip():
        return "Please type a question first.", ""

    result = ask(question.strip())

    sources_text = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources_text


# ---------------------------------------------------------------------------
# GRADIO UI
# ---------------------------------------------------------------------------

with gr.Blocks(title="The Unofficial Guide — UD CS Professor Reviews") as demo:

    # --- Header ---
    gr.Markdown("# 🎓 The Unofficial Guide — UD CS Professor Reviews")
    gr.Markdown(
        "Ask questions about CS professors at the University of Delaware — "
        "answers come from real student reviews"
    )

    # --- Input ---
    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. What do students say about Prof. Sethi's exams?",
    )

    # --- Submit button ---
    btn = gr.Button("Ask", variant="primary")

    # --- Outputs ---
    answer = gr.Textbox(label="Answer", lines=10)
    sources = gr.Textbox(label="Retrieved From", lines=4)

    # --- Wire up interactions ---
    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


# ---------------------------------------------------------------------------
# LAUNCH
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo.launch()
