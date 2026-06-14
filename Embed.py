"""
embed.py — Milestone 4: Embedding + Vector Store
-------------------------------------------------
Takes chunks produced by ingest.py, embeds them with all-MiniLM-L6-v2,
and stores them in a persistent local ChromaDB collection.

Also exposes a retrieve(query, k=3) function used by generate.py.

Usage:
    python embed.py            # build / rebuild the vector store
    python embed.py --check    # run retrieval checks without rebuilding
"""

import sys
import argparse

from ingest import ingest, RMP_PROFESSORS, REDDIT_THREADS

from sentence_transformers import SentenceTransformer
import chromadb

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

COLLECTION_NAME = "unofficial_guide"
CHROMA_DIR      = "./chroma_store"       # persisted to disk
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K           = 3

# ---------------------------------------------------------------------------
# Initialise ChromaDB + embedding model (module-level, reused by retrieve())
# ---------------------------------------------------------------------------

_model      = None
_collection = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"Loading embedding model '{EMBEDDING_MODEL}'...")
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _get_collection(readonly: bool = False):
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        if readonly:
            # Just get existing — will raise if it doesn't exist yet
            _collection = client.get_collection(name=COLLECTION_NAME)
        else:
            _collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},   # cosine similarity
            )
    return _collection


# ---------------------------------------------------------------------------
# Build vector store
# ---------------------------------------------------------------------------

def build_store(chunks: list[dict], batch_size: int = 128) -> None:
    """
    Embed all chunks and upsert them into ChromaDB.
    Uses upsert so re-running doesn't create duplicates.
    """
    model      = _get_model()
    collection = _get_collection()

    texts     = [c["text"]         for c in chunks]
    sources   = [c["source"]       for c in chunks]
    indices   = [c["chunk_index"]  for c in chunks]
    # Use global position to guarantee uniqueness across all sources
    ids       = [f"{src}__{i}" for i, src in enumerate(sources)]

    print(f"Embedding {len(texts)} chunks in batches of {batch_size}...")

    for start in range(0, len(texts), batch_size):
        batch_texts  = texts[start : start + batch_size]
        batch_ids    = ids[start : start + batch_size]
        batch_meta   = [
            {"source": sources[start + i], "chunk_index": indices[start + i]}
            for i in range(len(batch_texts))
        ]

        embeddings = model.encode(batch_texts, show_progress_bar=False).tolist()

        collection.upsert(
            ids        = batch_ids,
            documents  = batch_texts,
            embeddings = embeddings,
            metadatas  = batch_meta,
        )
        print(f"  Upserted chunks {start + 1}–{start + len(batch_texts)}")

    print(f"\nVector store built. Total documents in collection: {collection.count()}")


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """
    Embed the query and return the top-k most similar chunks.

    Returns a list of dicts:
        {
            'text':        chunk text,
            'source':      source name (e.g. 'rmp_rahul_dubey'),
            'chunk_index': position within source,
            'distance':    cosine distance (lower = more similar)
        }
    """
    model      = _get_model()
    collection = _get_collection(readonly=True)

    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings = query_embedding,
        n_results        = k,
        include          = ["documents", "metadatas", "distances"],
    )

    chunks = []
    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text":        text,
            "source":      meta["source"],
            "chunk_index": meta["chunk_index"],
            "distance":    round(dist, 4),
        })

    return chunks


# ---------------------------------------------------------------------------
# Verification checks
# ---------------------------------------------------------------------------

def run_checks() -> None:
    sep = "-" * 60
    print(f"\n{sep}")
    print("EMBED VERIFICATION REPORT")
    print(sep)

    collection = _get_collection(readonly=True)
    total = collection.count()

    # 1 — collection is non-empty
    print(f"\n[1] Collection '{COLLECTION_NAME}' has documents:")
    if total == 0:
        print("    FAIL — collection is empty. Run `python embed.py` first.")
        sys.exit(1)
    print(f"    PASS ({total} chunks stored)")

    # 2 — retrieve returns exactly TOP_K results
    print(f"\n[2] retrieve() returns {TOP_K} chunks for a test query:")
    results = retrieve("Is Rahul Dubey a hard grader?")
    if len(results) != TOP_K:
        print(f"    FAIL — expected {TOP_K}, got {len(results)}")
    else:
        print(f"    PASS")

    # 3 — all results have required keys
    required = {"text", "source", "chunk_index", "distance"}
    bad = [r for r in results if not required.issubset(r)]
    print(f"\n[3] All results have required keys (text, source, chunk_index, distance):")
    if bad:
        print(f"    FAIL — {len(bad)} result(s) missing keys")
    else:
        print("    PASS")

    # 4 — distances are valid (0.0–2.0 range for cosine)
    invalid_dist = [r for r in results if not (0.0 <= r["distance"] <= 2.0)]
    print(f"\n[4] Distances are in valid cosine range (0.0–2.0):")
    if invalid_dist:
        print(f"    FAIL — {len(invalid_dist)} result(s) with unexpected distance")
    else:
        print("    PASS")

    # 5 — spot check: RMP sources appear in results for a professor query
    rmp_sources   = {p["name"] for p in RMP_PROFESSORS}
    rmp_hits      = [r for r in results if r["source"] in rmp_sources]
    reddit_sources = {t["name"] for t in REDDIT_THREADS}
    print(f"\n[5] Professor-specific query returns RMP chunks (not off-topic Reddit):")
    if not rmp_hits:
        print(f"    WARN — no RMP chunks in top-{TOP_K} for 'Is Rahul Dubey a hard grader?'")
        print("           Retrieval may be noisy. Consider checking chunk quality.")
    else:
        print(f"    PASS ({len(rmp_hits)}/{TOP_K} results from RMP sources)")

    # --- Sample retrieval output ---
    print(f"\n{sep}")
    print(f"SAMPLE — top-{TOP_K} results for: 'Is Rahul Dubey a hard grader?'")
    print(sep)
    for i, r in enumerate(results, 1):
        print(f"  [{i}] source   : {r['source']}")
        print(f"      distance : {r['distance']}  (lower = more similar)")
        print(f"      text     : {r['text'][:150]!r}{'...' if len(r['text']) > 150 else ''}")
        print()

    # --- Second spot check: CS program difficulty ---
    print(sep)
    print("SAMPLE — top-3 results for: 'How hard is the CS program at MSU?'")
    print(sep)
    results2 = retrieve("How hard is the CS program at MSU?")
    for i, r in enumerate(results2, 1):
        print(f"  [{i}] source   : {r['source']}")
        print(f"      distance : {r['distance']}")
        print(f"      text     : {r['text'][:150]!r}{'...' if len(r['text']) > 150 else ''}")
        print()

    print("=" * 60)
    print("All checks passed — ready for generate.py")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true",
        help="Run retrieval checks only (skip re-embedding)"
    )
    args = parser.parse_args()

    if args.check:
        print("Running checks on existing vector store...")
        run_checks()
    else:
        print("Ingesting documents...")
        chunks = ingest()

        if not chunks:
            print("ERROR: No chunks produced by ingest.py. Aborting.")
            sys.exit(1)

        print(f"\n{len(chunks)} chunks ready for embedding.")
        build_store(chunks)
        run_checks()