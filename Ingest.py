

import os
import sys
import time
import json
import requests

CHUNK_SIZE = 200
OVERLAP    = 20
DOCUMENTS_DIR = "documents"   # fallback folder for manually saved .txt files


REDDIT_THREADS = [
    {
        "name": "reddit_cs_students",
        "url": "https://www.reddit.com/r/missouristate/comments/i0qp21/computer_science_students/.json",
    },
    {
        "name": "reddit_cs_at_msu",
        "url": "https://www.reddit.com/r/missouristate/comments/jmzz5g/computer_science_at_msu/.json",
    },
    {
        "name": "reddit_worth_it",
        "url": "https://www.reddit.com/r/missouristate/comments/sin703/will_missouri_state_university_be_worth_it_for_me/.json",
    },
]

RMP_PROFESSORS = [
    {"name": "rmp_jamil_saqel",    "id": "109481"},
    {"name": "rmp_rahul_dubey",    "id": "3092556"},
    {"name": "rmp_siming_liu",     "id": "2593599"},
    {"name": "rmp_hui_liu",        "id": "1071783"},
    {"name": "rmp_mukulika_ghosh", "id": "2879300"},
]

# RateMyProfessors GraphQL endpoint + query
RMP_GRAPHQL_URL = "https://www.ratemyprofessors.com/graphql"
RMP_REVIEWS_QUERY = """
query GetRatingsForTeacher($id: ID!, $count: Int!, $cursor: String) {
  node(id: $id) {
    ... on Teacher {
      firstName
      lastName
      department
      school { name }
      ratings(first: $count, after: $cursor) {
        edges {
          node {
            date
            class
            comment
            helpfulRating
            difficultyRating
            wouldTakeAgain
          }
        }
      }
    }
  }
}
"""

# ---------------------------------------------------------------------------
# Reddit scraping
# ---------------------------------------------------------------------------

def fetch_reddit_thread(name: str, url: str) -> list[str]:
    """
    Fetch all comments from a Reddit thread via the public .json API.
    Returns a list of comment body strings.
    """
    headers = {"User-Agent": "unofficial-guide-rag/1.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [WARN] Could not fetch Reddit thread '{name}': {e}")
        return []

    comments = []
    _extract_reddit_comments(data, comments)
    print(f"  [OK]   Reddit '{name}' — {len(comments)} comments fetched")
    return comments


def _extract_reddit_comments(data, out: list):
    """Recursively walk Reddit JSON and collect comment bodies."""
    if isinstance(data, list):
        for item in data:
            _extract_reddit_comments(item, out)
    elif isinstance(data, dict):
        kind = data.get("kind")
        payload = data.get("data", {})
        if kind == "t1":                          # comment node
            body = payload.get("body", "").strip()
            if body and body != "[deleted]" and body != "[removed]":
                out.append(body)
        # recurse into children / replies
        for key in ("children", "replies"):
            if key in payload:
                _extract_reddit_comments(payload[key], out)


# ---------------------------------------------------------------------------
# RateMyProfessors scraping
# ---------------------------------------------------------------------------

def fetch_rmp_reviews(name: str, professor_id: str, max_reviews: int = 50) -> list[str]:
    """
    Fetch reviews for one professor via the RMP unofficial GraphQL API.
    Returns a list of review comment strings.
    """
    # RMP encodes IDs as base64 "Teacher-<numeric_id>"
    import base64
    encoded_id = base64.b64encode(f"Teacher-{professor_id}".encode()).decode()

    headers = {
        "User-Agent":   "Mozilla/5.0 (compatible; unofficial-guide-rag/1.0)",
        "Content-Type": "application/json",
        "Referer":      "https://www.ratemyprofessors.com/",
    }
    payload = {
        "query": RMP_REVIEWS_QUERY,
        "variables": {"id": encoded_id, "count": max_reviews, "cursor": None},
    }

    try:
        resp = requests.post(RMP_GRAPHQL_URL, headers=headers,
                             json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
    except Exception as e:
        print(f"  [WARN] Could not fetch RMP professor '{name}' (id={professor_id}): {e}")
        return []

    try:
        edges = result["data"]["node"]["ratings"]["edges"]
        teacher = result["data"]["node"]
        prof_label = f"{teacher.get('firstName','')} {teacher.get('lastName','')}".strip()
        reviews = []
        for edge in edges:
            node = edge["node"]
            comment = node.get("comment", "").strip()
            course   = node.get("class", "").strip()
            if comment:
                # Prefix with professor name + course so retrieval has context
                prefix = f"[{prof_label}]"
                if course:
                    prefix += f" [{course}]"
                reviews.append(f"{prefix} {comment}")
        print(f"  [OK]   RMP '{name}' — {len(reviews)} reviews fetched")
        return reviews
    except (KeyError, TypeError) as e:
        print(f"  [WARN] Unexpected RMP response structure for '{name}': {e}")
        return []


# ---------------------------------------------------------------------------
# Manual fallback — load any .txt files in documents/
# ---------------------------------------------------------------------------

def load_manual_documents(documents_dir: str = DOCUMENTS_DIR) -> list[dict]:
    """
    Load any .txt files placed manually in documents/.
    Each file becomes one document with its filename as the source.
    """
    if not os.path.exists(documents_dir):
        return []
    docs = []
    for fname in sorted(os.listdir(documents_dir)):
        if fname.endswith(".txt"):
            fpath = os.path.join(documents_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                text = f.read().strip()
            if text:
                docs.append({"source": fname, "lines": text.splitlines()})
                print(f"  [OK]   Manual file '{fname}' loaded")
    return docs


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, source: str,
               chunk_size: int = CHUNK_SIZE,
               overlap: int = OVERLAP) -> list[dict]:
    """
    Split text into overlapping character-level chunks.
    Each chunk: {'text', 'source', 'chunk_index'}
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks = []
    step   = chunk_size - overlap
    start  = 0
    idx    = 0

    while start < len(text):
        chunk = text[start : start + chunk_size].strip()
        if chunk:
            chunks.append({"text": chunk, "source": source, "chunk_index": idx})
            idx += 1
        start += step

    return chunks


# ---------------------------------------------------------------------------
# Main ingest pipeline
# ---------------------------------------------------------------------------

def ingest() -> list[dict]:
    """
    Scrape all sources, chunk every piece of text, return flat list of chunks.
    Falls back to documents/ for any source that couldn't be scraped.
    """
    all_chunks: list[dict] = []

    # --- Reddit ---
    print("\nFetching Reddit threads...")
    for thread in REDDIT_THREADS:
        comments = fetch_reddit_thread(thread["name"], thread["url"])
        time.sleep(1)   # be polite — Reddit rate limits aggressive scrapers
        for comment in comments:
            all_chunks.extend(chunk_text(comment, source=thread["name"]))

    # --- RateMyProfessors ---
    print("\nFetching RateMyProfessors reviews...")
    for prof in RMP_PROFESSORS:
        reviews = fetch_rmp_reviews(prof["name"], prof["id"])
        time.sleep(1)
        for review in reviews:
            all_chunks.extend(chunk_text(review, source=prof["name"]))

    # --- Manual fallback ---
    manual_docs = load_manual_documents()
    if manual_docs:
        print(f"\nLoading {len(manual_docs)} manual document(s) from {DOCUMENTS_DIR}/...")
        for doc in manual_docs:
            full_text = "\n".join(doc["lines"])
            all_chunks.extend(chunk_text(full_text, source=doc["source"]))

    return all_chunks


# ---------------------------------------------------------------------------
# Verification checks
# ---------------------------------------------------------------------------

def run_checks(chunks: list[dict]) -> None:
    sep = "-" * 60
    print(f"\n{sep}")
    print("INGEST VERIFICATION REPORT")
    print(sep)

    # 1 — at least one chunk produced
    print(f"\n[1] Total chunks produced: {len(chunks)}")
    if not chunks:
        print("    FAIL — no chunks. Check network access or add files to documents/")
        sys.exit(1)
    print("    PASS")

    # 2 — required keys present on every chunk
    required = {"text", "source", "chunk_index"}
    bad = [i for i, c in enumerate(chunks) if not required.issubset(c)]
    print(f"\n[2] All chunks have required keys (text, source, chunk_index):")
    if bad:
        print(f"    FAIL — {len(bad)} chunk(s) missing keys")
        sys.exit(1)
    print("    PASS")

    # 3 — no chunk exceeds CHUNK_SIZE
    oversized = [c for c in chunks if len(c["text"]) > CHUNK_SIZE]
    print(f"\n[3] No chunk exceeds {CHUNK_SIZE} characters:")
    if oversized:
        print(f"    FAIL — {len(oversized)} oversized chunk(s)")
        for c in oversized[:3]:
            print(f"           source={c['source']}  len={len(c['text'])}")
    else:
        print("    PASS")

    # 4 — no empty text fields
    empty = [c for c in chunks if not c["text"].strip()]
    print(f"\n[4] No empty chunk text:")
    if empty:
        print(f"    FAIL — {len(empty)} empty chunk(s)")
    else:
        print("    PASS")

    # 5 — coverage: check every source produced at least 1 chunk
    expected_sources = {t["name"] for t in REDDIT_THREADS} | {p["name"] for p in RMP_PROFESSORS}
    found_sources    = {c["source"] for c in chunks}
    missing          = expected_sources - found_sources
    print(f"\n[5] All expected sources produced chunks:")
    if missing:
        print(f"    WARN — no chunks from: {missing}")
        print("           These sources failed to scrape. Add .txt files to documents/ as fallback.")
    else:
        print("    PASS")

    # --- Sample output ---
    print(f"\n{sep}")
    print("SAMPLE — first 5 chunks:")
    print(sep)
    for c in chunks[:5]:
        print(f"  source      : {c['source']}")
        print(f"  chunk_index : {c['chunk_index']}")
        print(f"  length      : {len(c['text'])} chars")
        print(f"  text        : {c['text'][:120]!r}{'...' if len(c['text']) > 120 else ''}")
        print()

    # --- Per-source breakdown ---
    print(sep)
    print("CHUNKS PER SOURCE:")
    print(sep)
    counts: dict[str, int] = {}
    for c in chunks:
        counts[c["source"]] = counts.get(c["source"], 0) + 1
    for src, n in sorted(counts.items()):
        status = "[scraped]" if src in expected_sources else "[manual]"
        print(f"  {status} {src:<42} {n:>4} chunks")

    print(f"\n{'=' * 60}")
    print(f"Total: {len(chunks)} chunks across {len(counts)} source(s)")
    print("Ready for embed.py")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Starting ingestion pipeline...")
    chunks = ingest()
    run_checks(chunks)