"""
app.py — Milestone 5: Gradio Interface
---------------------------------------
The user-facing web UI for the MSU CS Unofficial Guide.
Imports answer() from generate.py and displays results in a Gradio UI.

Usage:
    python app.py

Then open http://127.0.0.1:7860 in your browser.

Requirements:
    - .env file with GROQ_API_KEY=your_key_here
    - embed.py must have been run first (chroma_store/ must exist)
    - pip install gradio
"""

import gradio as gr
from generate import answer


# ---------------------------------------------------------------------------
# Gradio handler
# ---------------------------------------------------------------------------

def handle_query(query: str) -> tuple[str, str]:
    """
    Called by Gradio on every submission.
    Returns (answer_text, retrieved_chunks_display).
    """
    if not query.strip():
        return "Please enter a question.", ""

    answer_text, chunks = answer(query)

    # Format retrieved chunks for the collapsible panel
    if chunks:
        chunks_display = ""
        for i, c in enumerate(chunks, 1):
            chunks_display += f"**[{i}] {c['source']}** (distance: {c['distance']})\n"
            chunks_display += f"{c['text']}\n\n"
    else:
        chunks_display = "No chunks retrieved."

    return answer_text, chunks_display


# ---------------------------------------------------------------------------
# UI layout
# ---------------------------------------------------------------------------

with gr.Blocks(title="MSU CS Unofficial Guide") as demo:

    gr.Markdown("# 🎓 MSU CS Unofficial Guide")
    gr.Markdown(
        "Ask anything about CS professors, course difficulty, grading styles, "
        "and teaching styles — answers are grounded in real student reviews and Reddit posts."
    )

    query_box = gr.Textbox(
        label       = "Your question",
        placeholder = "e.g. What do students say about Rahul Dubey's exams?",
        lines       = 2,
    )

    submit_btn = gr.Button("Ask", variant="primary")

    answer_box = gr.Textbox(
        label       = "Answer",
        lines       = 8,
        interactive = False,
    )

    with gr.Accordion("Retrieved chunks (what the model saw)", open=False):
        chunks_box = gr.Markdown()

    # Wire up both the button click and pressing Enter in the text box
    submit_btn.click(
        fn      = handle_query,
        inputs  = [query_box],
        outputs = [answer_box, chunks_box],
    )
    query_box.submit(
        fn      = handle_query,
        inputs  = [query_box],
        outputs = [answer_box, chunks_box],
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo.launch()