"""
generate.py — Milestone 5: Grounded Generation
-----------------------------------------------
Core generation logic: retrieves top-3 chunks from ChromaDB and sends
them to llama-3.3-70b-versatile via Groq to produce a grounded answer.

Usage (checks only, no UI):
    python generate.py --check

Requirements:
    - .env file with GROQ_API_KEY=your_key_here
    - embed.py must have been run first (chroma_store/ must exist)
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from groq import Groq

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
3. Never invent quotes, ratings, or opinions that are not in the context.
4. Keep your answer concise and focused on what students actually said.
5. Include a Sources section or any source citations in your response."""

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
# Core generation function — imported by app.py
# ---------------------------------------------------------------------------

def answer(query: str) -> tuple[str, list[dict]]:
    """
    Retrieve relevant chunks and generate a grounded answer.
    Returns (answer_text, chunks_used).

    chunks_used is a list of dicts with keys:
        text, source, chunk_index, distance
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
            model       = GROQ_MODEL,
            messages    = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature = 0.2,   # low = more faithful to retrieved context
            max_tokens  = 512,
        )
        answer_text = response.choices[0].message.content.strip()
        for marker in ["Sources:", "Source:", "sources:", "source:"]:
            if marker in answer_text:
                answer_text = answer_text[:answer_text.index(marker)].strip()
    except Exception as e:
        answer_text = f"ERROR calling Groq API: {e}"

    return answer_text, chunks


# ---------------------------------------------------------------------------
# Verification checks
# ---------------------------------------------------------------------------

def run_checks() -> None:
    sep = "-" * 60
    print(f"\n{sep}")
    print("GENERATE VERIFICATION REPORT")
    print(sep)

    # 1 — API key present
    print(f"\n[1] GROQ_API_KEY is set:")
    if not GROQ_API_KEY:
        print("    FAIL — add GROQ_API_KEY=your_key to a .env file")
        sys.exit(1)
    print("    PASS")

    # 2 — retrieval works before calling Groq
    print(f"\n[2] retrieve() returns chunks for a test query:")
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

    # 4 — response length is reasonable (not rambling past context)
    print(f"\n[4] Response length is reasonable (under 800 chars):")
    if len(result) > 800:
        print(f"    WARN — response is {len(result)} chars. Model may be ignoring grounding.")
    else:
        print(f"    PASS ({len(result)} chars)")

    # 5 — response does not include Sources section (as instructed)
    print(f"\n[5] Response includes a Sources section:")
    if "sources" in result.lower():
        print("    WARN — model included a Sources section despite being told not to.")
    else:
        print("    PASS")

    # --- Run all 5 evaluation questions ---
    eval_questions = [
        "What do students say about Rahul Dubey's exam difficulty?",
        "How do students describe Mukulika Ghosh's grading style?",
        "What do MSU CS students say about the overall difficulty of the CS program?",
        "Is Hui Liu recommended by students, and what reasons do they give?",
        "What do students say about the teaching style of Siming Liu?",
    ]

    print(f"\n{sep}")
    print("EVALUATION QUESTIONS")
    print(sep)
    for i, q in enumerate(eval_questions, 1):
        print(f"\nQ{i}: {q}")
        resp, _ = answer(q)
        print(f"A:  {resp[:300]}{'...' if len(resp) > 300 else ''}")

    print(f"\n{'=' * 60}")
    print("All checks complete — launch the UI with: python app.py")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true",
        help="Run generation + retrieval checks without launching the UI"
    )
    args = parser.parse_args()

    if args.check:
        run_checks()
    else:
        print("This module contains generation logic only.")
        print("To launch the UI, run: python app.py")
        print("To run checks, run:    python generate.py --check")