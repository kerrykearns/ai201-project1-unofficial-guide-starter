"""
query.py — Milestone 5: Grounded Generation
The Unofficial Guide — CS Professor Reviews at University of Delaware

Pipeline stage: Retrieval → [Generation] → Answer + Sources

Run with:
    python query.py

Requires:
    pip install groq python-dotenv
    A .env file in the project root containing:  GROQ_API_KEY=your_key_here
"""

import os
from dotenv import load_dotenv
from groq import Groq

from retrieve import retrieve

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

load_dotenv()  # reads .env in the project root

MODEL = "llama-3.3-70b-versatile"
TEMPERATURE = 0.2  # low temperature → less creativity → fewer hallucinations
MAX_TOKENS = 500

TEST_QUESTIONS = [
    "What do students say about Prof. Sethi's attendance policy and lecture slides?",
    "Does Prof. Roosen give useful help when students are confused?",
    "What is the best restaurant in Paris?",  # must trigger refusal
]

# ---------------------------------------------------------------------------
# SYSTEM PROMPT  — grounding is enforced here
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a helpful assistant for the Unofficial Guide to CS professors at the University of Delaware.

GROUNDING RULES — these are absolute and non-negotiable:

1. You MUST answer ONLY using the information contained in the documents provided to you in each message. Do NOT use your general training knowledge about professors, universities, courses, or any other topic under any circumstances.

2. You MUST NOT invent, infer, or extrapolate information that does not appear explicitly in the provided documents. If a detail is not stated in the documents, it does not exist for the purposes of your answer.

3. If the provided documents do not contain enough information to answer the question, you MUST respond with exactly this sentence and nothing else:
   "I don't have enough information in my documents to answer that."

4. Every response that contains an answer MUST end with a section titled "Sources:" that lists the exact document filenames the answer came from.

5. Be specific — reference what students actually said, using their exact words where possible, and attribute claims to the source document.

You are a strict retrieval assistant. You are NOT a general-purpose chatbot."""


# ---------------------------------------------------------------------------
# CONTEXT BUILDER
# ---------------------------------------------------------------------------


def build_context(chunks: list[dict]) -> str:
    """
    Formats retrieved chunks into a labeled context string passed to the LLM.

    Each chunk is prefixed with its source filename so the model can see
    which document each piece of evidence came from:

        [From Adarsh Sethi.txt]:
        chunk text here...

        [From Andrew Roosen.txt]:
        chunk text here...
    """
    parts = []
    for chunk in chunks:
        label = f"[From {chunk['source']}]:"
        parts.append(f"{label}\n{chunk['text'].strip()}")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# CORE ASK FUNCTION
# ---------------------------------------------------------------------------


def ask(question: str) -> dict:
    """
    Full RAG pipeline: retrieve → build context → call LLM → return result.

    Parameters
    ----------
    question : the user's natural-language question

    Returns
    -------
    A dict with exactly two keys:
        'answer'  : the full LLM response string
        'sources' : a Python list of unique source filenames (programmatically
                    collected from the retrieved chunks — not extracted from
                    the LLM's text output)
    """
    # --- 1. Retrieve the top-5 most relevant chunks ---
    chunks = retrieve(question, top_k=5)

    # --- 2. Collect unique source filenames in Python (guaranteed attribution) ---
    # This is done HERE in code, not by asking the LLM to list its sources.
    # The LLM might hallucinate or forget sources; this list never will.
    seen = set()
    unique_sources = []
    for chunk in chunks:
        src = chunk["source"]
        if src not in seen:
            seen.add(src)
            unique_sources.append(src)

    # --- 3. Build the labeled context string ---
    context = build_context(chunks)

    # --- 4. Compose the user message: context + question ---
    user_message = (
        f"Here are the relevant documents:\n\n"
        f"{context}\n\n"
        f"---\n"
        f"Question: {question}"
    )

    # --- 5. Call the Groq LLM ---
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    completion = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    answer = completion.choices[0].message.content.strip()

    return {
        "answer": answer,
        "sources": unique_sources,
    }


# ---------------------------------------------------------------------------
# DIRECT EXECUTION — runs the 3 test questions
# ---------------------------------------------------------------------------


def main():
    print("\nquery.py — Grounded Generation Test")
    print("=" * 60)

    for question in TEST_QUESTIONS:
        print(f"\nQUESTION: {question}")
        print("-" * 60)

        result = ask(question)

        print(f"ANSWER:\n{result['answer']}")
        print(f"\nSOURCES (programmatic):")
        for src in result["sources"]:
            print(f"  • {src}")
        print("=" * 60)


if __name__ == "__main__":
    main()
