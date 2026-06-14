
import gradio as gr
from generate import answer


def handle_query(query: str) -> str:
    if not query.strip():
        return "Please enter a question."
    answer_text, _ = answer(query)
    return answer_text


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

    submit_btn.click(fn=handle_query, inputs=[query_box], outputs=[answer_box])
    query_box.submit(fn=handle_query, inputs=[query_box], outputs=[answer_box])


if __name__ == "__main__":
    demo.launch()