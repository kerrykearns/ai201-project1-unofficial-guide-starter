"""
embed.py — Milestone 4: Embedding + Vector Store
The Unofficial Guide — CS Professor Reviews at University of Delaware

Pipeline stage: Chunking → [Embedding] → [Vector Store] → Retrieval

Run with:
    python embed.py

Requires:
    pip install sentence-transformers chromadb
"""

import chromadb
from sentence_transformers import SentenceTransformer

from ingest import run_pipeline

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384-dim, runs locally, no API cost
COLLECTION_NAME = "unofficial_guide"
CHROMA_DB_PATH = "./chroma_db"  # persisted on disk in project root
BATCH_SIZE = 50  # embed this many chunks per batch


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def build_chroma_collection(chunks, model):
    """
    Creates (or wipes and recreates) the ChromaDB collection called
    'unofficial_guide', then embeds every chunk and upserts it.

    Each stored document has:
        - id       : a unique string  "chunk_0", "chunk_1", …
        - document : the raw chunk text  (what ChromaDB indexes for search)
        - embedding: the 384-float vector produced by all-MiniLM-L6-v2
        - metadata : {"source": filename, "start_char": int}

    Returns the live collection object.
    """
    # ------------------------------------------------------------------
    # 1. Connect to (or create) the persistent database on disk
    # ------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("EMBED.PY — Embedding + Vector Store")
    print(f"{'='*60}")

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    print(f"\n  ChromaDB path  : {CHROMA_DB_PATH}")

    # ------------------------------------------------------------------
    # 2. Delete existing collection so every rebuild is clean / idempotent
    # ------------------------------------------------------------------
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)
        print(f"  Deleted old collection '{COLLECTION_NAME}' — rebuilding fresh.")

    collection = client.create_collection(
        name=COLLECTION_NAME,
        # cosine distance so scores range 0 (identical) → 2 (opposite)
        # in practice relevant results sit well below 0.5
        metadata={"hnsw:space": "cosine"},
    )
    print(f"  Created collection '{COLLECTION_NAME}'.\n")

    # ------------------------------------------------------------------
    # 3. Embed and insert in batches
    # ------------------------------------------------------------------
    total = len(chunks)
    print(f"  Embedding {total} chunks in batches of {BATCH_SIZE} …\n")

    for batch_start in range(0, total, BATCH_SIZE):
        batch = chunks[batch_start : batch_start + BATCH_SIZE]

        texts = [c["text"] for c in batch]
        ids = [f"chunk_{batch_start + i}" for i in range(len(batch))]
        metadatas = [
            {"source": c["source"], "start_char": c["start_char"]} for c in batch
        ]

        # encode() returns a numpy array of shape (n_chunks, 384)
        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        batch_end = min(batch_start + BATCH_SIZE, total)
        print(
            f"  Stored chunks {batch_start:>4} – {batch_end - 1:>4}  "
            f"({batch_end}/{total})"
        )

    return collection


def verify_storage(collection):
    """
    Spot-checks the stored collection:
      - Confirms the total count matches what we inserted.
      - Prints the metadata of the first 3 entries so you can confirm
        'source' and 'start_char' are attached correctly.
    """
    count = collection.count()
    print(f"\n  ✓ Total chunks stored in ChromaDB: {count}")

    sample = collection.get(
        ids=["chunk_0", "chunk_1", "chunk_2"], include=["metadatas", "documents"]
    )
    print("\n  --- Metadata spot-check (first 3 chunks) ---")
    for i, (meta, doc) in enumerate(zip(sample["metadatas"], sample["documents"])):
        print(f"\n  chunk_{i}")
        print(f"    source     : {meta['source']}")
        print(f"    start_char : {meta['start_char']}")
        print(f"    text[:80]  : {doc[:80].strip()!r}")
    print()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------


def main():
    # Stage 3 output — 175 chunk dicts with text / source / start_char
    print("\nRunning ingest pipeline …")
    chunks = run_pipeline()
    print(f"\n  ingest.run_pipeline() returned {len(chunks)} chunks.")

    # Load embedding model (downloads once, cached in ~/.cache/huggingface)
    print(f"\n  Loading embedding model '{EMBEDDING_MODEL}' …")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(
        f"  Model loaded. Embedding dimension: {model.get_sentence_embedding_dimension()}"
    )

    # Build the vector store
    collection = build_chroma_collection(chunks, model)

    # Quick verification
    verify_storage(collection)

    print("=" * 60)
    print(f"embed.py complete — {collection.count()} chunks ready for retrieval.")
    print("=" * 60)


if __name__ == "__main__":
    main()
