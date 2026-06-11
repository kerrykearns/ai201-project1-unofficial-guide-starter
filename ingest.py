"""
ingest.py — Milestone 3: Document Ingestion, Cleaning, and Chunking
The Unofficial Guide — CS Professor Reviews at University of Delaware

Pipeline: Document Ingestion → Cleaning → Chunking → (next: Embedding)
"""

import os
import re
import random

# ---------------------------------------------------------------------------
# STAGE 1: LOADING
# ---------------------------------------------------------------------------


def load_documents(folder_path="documents"):
    """
    Walks the given folder, reads every .txt file, and returns a list of
    dicts with keys:
        - 'filename': the bare filename (e.g. 'Greg Silber.txt')
        - 'raw_text': the full, unmodified string read from disk
    Also prints the filename and character count for every file loaded so
    you can spot-check that all 10 sources came in correctly.
    """
    documents = []

    if not os.path.isdir(folder_path):
        raise FileNotFoundError(
            f"Could not find folder '{folder_path}'. "
            "Make sure you run this script from the project root and that "
            "the documents/ folder exists there."
        )

    txt_files = sorted(f for f in os.listdir(folder_path) if f.endswith(".txt"))

    if not txt_files:
        raise ValueError(f"No .txt files found inside '{folder_path}'.")

    print(f"\n{'='*60}")
    print(f"STAGE 1 — LOADING ({len(txt_files)} files found)")
    print(f"{'='*60}")

    for filename in txt_files:
        filepath = os.path.join(folder_path, filename)
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            raw_text = fh.read()
        print(f"  Loaded: {filename:40s}  ({len(raw_text):,} chars)")
        documents.append({"filename": filename, "raw_text": raw_text})

    print(f"\n  Total documents loaded: {len(documents)}")
    return documents


# ---------------------------------------------------------------------------
# STAGE 2: CLEANING
# ---------------------------------------------------------------------------


def clean_text(raw_text):
    """
    Takes a raw string and returns a cleaned string suitable for chunking.
    Steps applied in order:
      1. Decode common HTML entities.
      2. Strip any residual HTML tags.
      3. Remove lines that look like navigation / boilerplate.
      4. Collapse runs of blank lines to a single blank line.
      5. Strip leading/trailing whitespace from every line.
      6. Strip the whole document's leading/trailing whitespace.
    """
    text = raw_text

    # --- 1. HTML entity decoding ---
    entity_map = {
        "&amp;": "&",
        "&nbsp;": " ",
        "&#39;": "'",
        "&quot;": '"',
        "&lt;": "<",
        "&gt;": ">",
        "&apos;": "'",
        "&#x27;": "'",
        "&#x2F;": "/",
        "&#34;": '"',
        "&#38;": "&",
    }
    for entity, replacement in entity_map.items():
        text = text.replace(entity, replacement)

    # --- 2. Strip HTML tags ---
    text = re.sub(r"<[^>]+>", " ", text)

    # --- 3. Remove boilerplate / navigation lines ---
    boilerplate_patterns = [
        r"^\s*share\s*$",
        r"^\s*helpful\s*\(\d+\)\s*$",
        r"^\s*not helpful\s*\(\d+\)\s*$",
        r"^\s*report\s*$",
        r"^\s*flag\s*$",
        r"^\s*cookie(s)?\s*$",
        r"^\s*accept all\s*$",
        r"^\s*privacy policy\s*$",
        r"^\s*terms of (use|service)\s*$",
        r"^\s*rate my professor(s)?\s*$",
        r"^\s*add a professor\s*$",
        r"^\s*compare professors?\s*$",
        r"^\s*school ratings?\s*$",
        r"^\s*sign (in|up)\s*$",
        r"^\s*log (in|out)\s*$",
        r"^\s*home\s*$",
        r"^\s*search\s*$",
        r"^\s*(like|dislike)\s*$",
        r"^\s*\d+\s*(like|helpful|students found this helpful)\s*$",
        r"^\s*loading\s*\.{0,3}\s*$",
        r"^\s*for credit[:\s]*(yes|no)\s*$",
        r"^\s*attendance[:\s]*(mandatory|not mandatory)\s*$",
        r"^\s*grade[:\s]*[a-fA-F][+-]?\s*$",
        r"^\s*textbook[:\s]*(yes|no)\s*$",
        r"^\s*would take again[:\s]*(yes|no)\s*$",
    ]
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        if not any(re.match(pat, line, re.IGNORECASE) for pat in boilerplate_patterns):
            cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)

    # --- 4. Collapse multiple blank lines into one ---
    text = re.sub(r"\n{3,}", "\n\n", text)

    # --- 5. Strip leading/trailing whitespace from each line ---
    text = "\n".join(line.strip() for line in text.splitlines())

    # --- 6. Strip the whole document ---
    text = text.strip()

    return text


def clean_documents(documents):
    """
    Applies clean_text() to every document in the list.
    Adds a 'clean_text' key to each document dict.
    Prints a full cleaned version of the first document so you can read it
    and confirm the cleaning is working before chunking begins.
    """
    print(f"\n{'='*60}")
    print("STAGE 2 — CLEANING")
    print(f"{'='*60}")

    for doc in documents:
        doc["clean_text"] = clean_text(doc["raw_text"])

    # Print the first document in full for manual inspection
    preview_doc = documents[0]
    print(f"\n--- Full cleaned text for: {preview_doc['filename']} ---\n")
    print(preview_doc["clean_text"])
    print(
        f"\n--- End of preview ({len(preview_doc['clean_text']):,} chars after cleaning) ---"
    )

    return documents


# ---------------------------------------------------------------------------
# STAGE 3: CHUNKING
# ---------------------------------------------------------------------------


def chunk_text(text, source, chunk_size=300, overlap=50):
    """
    Splits a single cleaned text string into overlapping chunks using plain
    Python string slicing (no external libraries).

    Parameters
    ----------
    text       : the cleaned document string
    source     : the filename this text came from (stored in every chunk)
    chunk_size : maximum characters per chunk (default 300, per spec)
    overlap    : characters of overlap between consecutive chunks (default 50)

    Returns a list of dicts, each with:
        - 'text'       : the chunk string
        - 'source'     : the originating filename
        - 'start_char' : character offset of this chunk in the full document

    How the overlap works
    ---------------------
    After cutting a chunk that starts at position `pos`, the next chunk
    starts at  pos + chunk_size - overlap  (i.e. we step forward by
    chunk_size MINUS overlap so the tail of the previous chunk is repeated
    at the head of the next one).  That shared 50-character window means a
    sentence that straddles a boundary will appear in full in at least one
    of the two adjacent chunks.

    Chunks shorter than 20 characters are discarded as fragments.
    """
    chunks = []
    pos = 0
    step = chunk_size - overlap  # 250 chars forward each iteration

    while pos < len(text):
        end = pos + chunk_size
        chunk_str = text[pos:end]

        # Discard tiny fragments (whitespace-only or near-empty)
        if len(chunk_str.strip()) >= 20:
            chunks.append(
                {
                    "text": chunk_str,
                    "source": source,
                    "start_char": pos,
                }
            )

        pos += step

    return chunks


def chunk_documents(documents, chunk_size=300, overlap=50):
    """
    Calls chunk_text() for every cleaned document and concatenates all
    resulting chunk dicts into a single flat list.
    """
    all_chunks = []
    for doc in documents:
        doc_chunks = chunk_text(
            text=doc["clean_text"],
            source=doc["filename"],
            chunk_size=chunk_size,
            overlap=overlap,
        )
        all_chunks.extend(doc_chunks)
    return all_chunks


# ---------------------------------------------------------------------------
# STAGE 4: VERIFICATION
# ---------------------------------------------------------------------------


def verify_chunks(all_chunks, sample_size=5):
    """
    Prints:
      - Total chunk count with a warning if it falls outside [50, 2000].
      - 5 randomly selected sample chunks, each clearly labelled.
    """
    total = len(all_chunks)

    print(f"\n{'='*60}")
    print("STAGE 4 — VERIFICATION")
    print(f"{'='*60}")
    print(f"\n  Total chunks produced: {total:,}")

    if total < 50:
        print(
            f"  WARNING: Only {total} chunks — expected at least 50. "
            "Check that your documents/ folder has all 10 .txt files and "
            "that none are empty."
        )
    elif total > 2000:
        print(
            f"  WARNING: {total} chunks exceeds 2,000. "
            "Consider increasing chunk_size or verify documents aren't duplicated."
        )
    else:
        print(f"  Chunk count is within the expected range [50, 2000].")

    print(f"\n  --- {sample_size} Randomly Sampled Chunks ---")
    samples = random.sample(all_chunks, min(sample_size, total))
    for i, chunk in enumerate(samples, 1):
        print(f"\n  {'─'*56}")
        print(f"  Sample {i}")
        print(f"  Source    : {chunk['source']}")
        print(f"  start_char: {chunk['start_char']}")
        print(f"  Length    : {len(chunk['text'])} chars")
        print(f"  Text      :\n")
        for line in chunk["text"].splitlines():
            print(f"    {line}")
    print(f"\n  {'─'*56}")


# ---------------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------------


def run_pipeline(folder_path="documents"):
    """
    Orchestrates all four stages and returns the complete list of chunk dicts.
    Other scripts (e.g. embed.py for Milestone 4) should import and call this
    function:

        from ingest import run_pipeline
        chunks = run_pipeline()

    Each returned dict has the keys:  text, source, start_char
    """
    # Stage 1 — Load
    documents = load_documents(folder_path)

    # Stage 2 — Clean
    documents = clean_documents(documents)

    # Stage 3 — Chunk (300-char chunks, 50-char overlap, per planning.md)
    all_chunks = chunk_documents(documents, chunk_size=300, overlap=50)

    # Stage 4 — Verify + sample
    verify_chunks(all_chunks, sample_size=5)

    return all_chunks


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    chunks = run_pipeline()
    print(f"\nrun_pipeline() complete — {len(chunks):,} chunks ready for embedding.\n")
