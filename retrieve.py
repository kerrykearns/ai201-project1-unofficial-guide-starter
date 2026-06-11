"""
retrieve.py — Milestone 4: Semantic Retrieval
The Unofficial Guide — CS Professor Reviews at University of Delaware

Pipeline stage: Vector Store → [Retrieval] → Generation

Run with:
    python retrieve.py

Requires:
    pip install sentence-transformers chromadb
    (embed.py must have been run first to populate chroma_db/)
"""

import chromadb
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# CONFIGURATION  (must match embed.py)
# ---------------------------------------------------------------------------

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "unofficial_guide"
CHROMA_DB_PATH = "./chroma_db"

# Distance threshold above which we warn that a result may be a weak match.
# all-MiniLM-L6-v2 with cosine distance: 0–0.3 strong, 0.3–0.5 acceptable,
# >0.5 suspect.
WEAK_MATCH_THRESHOLD = 0.5

# Evaluation queries from planning.md
EVAL_QUERIES = [
    "What do students say about Prof. Sethi's attendance and lecture slides?",
    "What is Prof. Roosen's teaching style and how do students succeed in his class?",
    "What do students say about Prof. Silber's workload and grading?",
]


# ---------------------------------------------------------------------------
# CORE RETRIEVAL FUNCTION
# ---------------------------------------------------------------------------


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """
    Embeds `query` with all-MiniLM-L6-v2 and returns the `top_k` most
    semantically similar chunks from the ChromaDB collection.

    Each returned dict contains:
        - 'text'     : the chunk string
        - 'source'   : the originating filename  (e.g. 'Adarsh Sethi.txt')
        - 'distance' : cosine distance (float, lower = more similar)

    Parameters
    ----------
    query  : natural-language question or keyword string
    top_k  : number of chunks to return (default 5, per planning.md spec)

    Raises
    ------
    RuntimeError if the collection does not exist — run embed.py first.
    """
    # --- Load model and collection (lazy-loaded once per process) ---
    model = _get_model()
    collection = _get_collection()

    # --- Embed the query (same model as used at index time) ---
    query_embedding = model.encode(query).tolist()

    # --- Query ChromaDB ---
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    # --- Unpack and normalise into a clean list of dicts ---
    chunks = []
    documents = results["documents"][0]  # outer list = one query
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        chunks.append(
            {
                "text": doc,
                "source": meta.get("source", "unknown"),
                "distance": dist,
            }
        )

    return chunks


# ---------------------------------------------------------------------------
# MODULE-LEVEL SINGLETONS  (model + collection loaded once)
# ---------------------------------------------------------------------------

_model = None
_collection = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        existing = [c.name for c in client.list_collections()]
        if COLLECTION_NAME not in existing:
            raise RuntimeError(
                f"Collection '{COLLECTION_NAME}' not found in '{CHROMA_DB_PATH}'. "
                "Run embed.py first to build the vector store."
            )
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


# ---------------------------------------------------------------------------
# PRETTY-PRINT HELPER
# ---------------------------------------------------------------------------


def print_results(query: str, results: list[dict]) -> None:
    """
    Prints retrieval results in a readable, clearly labelled format.
    Warns if any distance score exceeds WEAK_MATCH_THRESHOLD.
    """
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"{'='*60}")

    weak_matches = []

    for rank, chunk in enumerate(results, start=1):
        print(f"\n  Result {rank}")
        print(f"  {'─'*54}")
        print(f"  Source   : {chunk['source']}")
        print(f"  Distance : {chunk['distance']:.3f}", end="")

        if chunk["distance"] > WEAK_MATCH_THRESHOLD:
            print("  ⚠  (may be a weak match)", end="")
            weak_matches.append(rank)
        print()

        print(f"  Text     :\n")
        for line in chunk["text"].splitlines():
            print(f"    {line}")

    print(f"\n  {'─'*54}")

    if weak_matches:
        print(
            f"\n  NOTE: Result(s) {weak_matches} have distance > {WEAK_MATCH_THRESHOLD}. "
            "These chunks may not be relevant — see guidance in the README."
        )


# ---------------------------------------------------------------------------
# DIRECT EXECUTION — runs the 3 evaluation queries
# ---------------------------------------------------------------------------


def main():
    print("\nretrieve.py — Semantic Retrieval Test")
    print("Loading embedding model and connecting to ChromaDB …")

    # Warm up singletons before timing
    _get_model()
    _get_collection()

    print(
        f"Connected to collection '{COLLECTION_NAME}' "
        f"({_get_collection().count()} chunks).\n"
    )

    for query in EVAL_QUERIES:
        results = retrieve(query, top_k=5)
        print_results(query, results)

    print(f"\n{'='*60}")
    print("retrieve.py complete.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
