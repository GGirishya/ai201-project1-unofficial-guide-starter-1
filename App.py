"""
app.py — Milestone 5: Gradio Interface
---------------------------------------
The user-facing web UI for the MSU CS Unofficial Guide.
Imports answer() from generate.py and displays results in a Gradio UI.

Usage:
    python app.py

Then open http://127.0.0.1:7860 in your browser.
"""

import gradio as gr
from generate import answer

# ---------------------------------------------------------------------------
# Source name → URL mapping
# ---------------------------------------------------------------------------

SOURCE_LINKS = {
    "rmp_jamil_saqel":    "https://www.ratemyprofessors.com/professor/109481",
    "rmp_rahul_dubey":    "https://www.ratemyprofessors.com/professor/3092556",
    "rmp_siming_liu":     "https://www.ratemyprofessors.com/professor/2593599",
    "rmp_hui_liu":        "https://www.ratemyprofessors.com/professor/1071783",
    "rmp_mukulika_ghosh": "https://www.ratemyprofessors.com/professor/2879300",
    "reddit_cs_students": "https://www.reddit.com/r/missouristate/comments/i0qp21/computer_science_students/",
    "reddit_cs_at_msu":   "https://www.reddit.com/r/missouristate/comments/jmzz5g/computer_science_at_msu/",
    "reddit_worth_it":    "https://www.reddit.com/r/missouristate/comments/sin703/will_missouri_state_university_be_worth_it_for_me/",
}

SOURCE_LABELS = {
    "rmp_jamil_saqel":    "RateMyProfessors — Jamil Saqel",
    "rmp_rahul_dubey":    "RateMyProfessors — Rahul Dubey",
    "rmp_siming_liu":     "RateMyProfessors — Siming Liu",
    "rmp_hui_liu":        "RateMyProfessors — Hui Liu",
    "rmp_mukulika_ghosh": "RateMyProfessors — Mukulika Ghosh",
    "reddit_cs_students": "r/missouristate — Computer Science Students?",
    "reddit_cs_at_msu":   "r/missouristate — Computer Science at MSU",
    "reddit_worth_it":    "r/missouristate — Will Missouri State be worth it?",
}


def format_source_links(chunks: list[dict]) -> str:
    """
    Build a markdown string of unique source links from retrieved chunks.
    """
    seen = set()
    links = []
    for chunk in chunks:
        src = chunk["source"]
        if src not in seen:
            seen.add(src)
            url   = SOURCE_LINKS.get(src, "#")
            label = SOURCE_LABELS.get(src, src)
            links.append(f"- [{label}]({url})")
    return "\n".join(links) if links else ""


def handle_query(query: str) -> tuple[str, str]:
    if not query.strip():
        return "Please enter a question.", ""

    answer_text, chunks = answer(query)
    sources_md = format_source_links(chunks)
    return answer_text, sources_md


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

    gr.Markdown("**Sources**")
    sources_box = gr.Markdown()

    submit_btn.click(fn=handle_query, inputs=[query_box], outputs=[answer_box, sources_box])
    query_box.submit(fn=handle_query, inputs=[query_box], outputs=[answer_box, sources_box])


if __name__ == "__main__":
    demo.launch()