"""
generate.py — Milestone 5: Generation + Gradio Interface
---------------------------------------------------------
Retrieves top-3 chunks from ChromaDB, sends them to llama-3.3-70b-versatile
via the Groq API, and returns a grounded answer that cites its sources.

The system prompt explicitly instructs the model to answer ONLY from the
retrieved context — if the answer isn't there, it must say so.

Usage:
    python generate.py            # launch Gradio UI
    python generate.py --check    # run generation checks without launching UI

Requirements:
    - .env file with GROQ_API_KEY=your_key_here
    - embed.py must have been run first (chroma_store/ must exist)
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from groq import Groq
import gradio as gr

from embed import retrieve

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = "llama-3.3-70b-versatile"
TOP_K        = 3

# ---------------------------------------------------------------------------
# System prompt — grounding instruction
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an unofficial guide for Computer Science students at Missouri State University (MSU).

You answer questions about CS professors, course difficulty, grading styles, exam structures, and teaching styles — based ONLY on the student reviews and Reddit comments provided to you as context.

Rules you must follow:
1. Answer using ONLY information from the provided context. Do not use any outside knowledge.
2. If the context does not contain enough information to answer the question, say: "I don't have enough reviews to answer that confidently."
3. After your answer, always list the sources you used under a "Sources:" heading, using the source names provided in the context.
4. Never invent quotes, ratings, or opinions that are not in the context.
5. Keep your answer concise and focused on what students actually said."""

# ---------------------------------------------------------------------------
# Format context for the prompt
# ---------------------------------------------------------------------------

def format_context(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a numbered context block for the prompt.
    Each chunk includes its source name so the model can cite it.
    """
    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(f"[{i}] (source: {chunk['source']})")
        lines.append(chunk["text"])
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core generation function
# ---------------------------------------------------------------------------

def answer(query: str) -> tuple[str, list[dict]]:
    """
    Retrieve relevant chunks and generate a grounded answer.
    Returns (answer_text, chunks_used).
    """
    if not GROQ_API_KEY:
        return (
            "ERROR: GROQ_API_KEY not found. Add it to a .env file:\n  GROQ_API_KEY=your_key_here",
            []
        )

    chunks = retrieve(query, k=TOP_K)

    if not chunks:
        return "No relevant reviews found for that question.", []

    context = format_context(chunks)

    user_message = f"""Context (student reviews and Reddit comments):
{context}

Question: {query}"""

    client = Groq(api_key=GROQ_API_KEY)

    try:
        response = client.chat.completions.create(
            model    = GROQ_MODEL,
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature = 0.2,    # low temperature = more faithful to context
            max_tokens  = 512,
        )
        answer_text = response.choices[0].message.content.strip()
    except Exception as e:
        answer_text = f"ERROR calling Groq API: {e}"

    return answer_text, chunks


# ---------------------------------------------------------------------------
# Gradio interface
# ---------------------------------------------------------------------------

def gradio_answer(query: str) -> tuple[str, str]:
    """
    Wrapper for Gradio — returns (answer, retrieved_chunks_display).
    """
    if not query.strip():
        return "Please enter a question.", ""

    answer_text, chunks = answer(query)

    # Format retrieved chunks for display in the UI
    chunks_display = ""
    for i, c in enumerate(chunks, 1):
        chunks_display += f"**[{i}] {c['source']}** (distance: {c['distance']})\n"
        chunks_display += f"{c['text']}\n\n"

    return answer_text, chunks_display


def launch_ui() -> None:
    with gr.Blocks(title="MSU CS Unofficial Guide") as demo:
        gr.Markdown("# 🎓 MSU CS Unofficial Guide")
        gr.Markdown(
            "Ask about professors, course difficulty, grading styles, and teaching styles "
            "based on real student reviews and Reddit posts."
        )

        with gr.Row():
            query_box = gr.Textbox(
                label       = "Your question",
                placeholder = "e.g. What do students say about Rahul Dubey's exams?",
                lines       = 2,
            )

        submit_btn = gr.Button("Ask", variant="primary")

        with gr.Row():
            answer_box = gr.Textbox(
                label    = "Answer",
                lines    = 8,
                interactive = False,
            )

        with gr.Accordion("Retrieved chunks (what the model saw)", open=False):
            chunks_box = gr.Markdown()

        submit_btn.click(
            fn      = gradio_answer,
            inputs  = [query_box],
            outputs = [answer_box, chunks_box],
        )
        query_box.submit(
            fn      = gradio_answer,
            inputs  = [query_box],
            outputs = [answer_box, chunks_box],
        )

    demo.launch()


# ---------------------------------------------------------------------------
# Verification checks
# ---------------------------------------------------------------------------

def run_checks() -> None:
    sep = "-" * 60
    print(f"\n{sep}")
    print("GENERATE VERIFICATION REPORT")
    print(sep)

    # 1 — API key is present
    print(f"\n[1] GROQ_API_KEY is set:")
    if not GROQ_API_KEY:
        print("    FAIL — add GROQ_API_KEY=your_key to a .env file")
        sys.exit(1)
    print("    PASS")

    # 2 — retrieve() returns chunks before we even call Groq
    print(f"\n[2] retrieve() works for a test query:")
    chunks = retrieve("What do students say about Rahul Dubey?")
    if not chunks:
        print("    FAIL — no chunks returned. Run embed.py first.")
        sys.exit(1)
    print(f"    PASS ({len(chunks)} chunks)")

    # 3 — full answer() call succeeds
    print(f"\n[3] answer() returns a non-empty response:")
    result, used_chunks = answer("What do students say about Rahul Dubey?")
    if not result or result.startswith("ERROR"):
        print(f"    FAIL — {result}")
        sys.exit(1)
    print("    PASS")

    # 4 — grounding check: response should not be longer than ~800 chars
    #     (a sign the model ignored context and rambled)
    print(f"\n[4] Response length is reasonable (under 800 chars):")
    if len(result) > 800:
        print(f"    WARN — response is {len(result)} chars. Model may be ignoring grounding.")
    else:
        print(f"    PASS ({len(result)} chars)")

    # 5 — response contains "Sources:" (model followed citation instruction)
    print(f"\n[5] Response includes a Sources section:")
    if "sources" not in result.lower():
        print("    WARN — no 'Sources:' found. Model may not be citing context.")
    else:
        print("    PASS")

    # --- Run all 5 evaluation questions ---
    print(f"\n{sep}")
    print("EVALUATION QUESTIONS")
    print(sep)

    eval_questions = [
        "What do students say about Rahul Dubey's exam difficulty?",
        "How do students describe Mukulika Ghosh's grading style?",
        "What do MSU CS students say about the overall difficulty of the CS program?",
        "Is Hui Liu recommended by students, and what reasons do they give?",
        "What do students say about the teaching style of Siming Liu?",
    ]

    for i, q in enumerate(eval_questions, 1):
        print(f"\nQ{i}: {q}")
        resp, _ = answer(q)
        print(f"A:  {resp[:300]}{'...' if len(resp) > 300 else ''}")

    print(f"\n{'=' * 60}")
    print("All checks complete — ready to launch UI with: python generate.py")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true",
        help="Run generation checks without launching the Gradio UI"
    )
    args = parser.parse_args()

    if args.check:
        run_checks()
    else:
        launch_ui()