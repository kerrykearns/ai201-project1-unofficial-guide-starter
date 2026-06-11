# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

This system covers student reviews of CS professors at the University of Delaware. This knowledge is valuable because students make critical decisions about which courses to take and which professors to learn from, but official university sources  course catalogs, department websites, and syllabi contain none of this information. Teaching style, exam difficulty, grading fairness, and workload are invisible through official channels. The only way to access this knowledge is through scattered student-to-student platforms like Rate My Professors, which are hard to search in aggregate or compare across professors. This system makes that knowledge queryable in plain language.
---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Rate My Professor website|Adarsh Srthi.txt | documents/Adarsh Sethi.txt|
| 2 | Rate My Professor website|Andrew Roosen.txt | documents/Andrew Roosen.txt|
| 3 | Rate My Professor website|Austin Bart.txt | documents/Austin Bart.txt|
| 4 | Rate My Professor website| Christopher Rasmussen.txt| documents/Christopher Rasmussen.txt|
| 5 | Rate My Professor website| Nazim Karaca.txt| documents/Nazim Karaca.txt|
| 6 | Rate My Professor website| Greg Silber_reviews.txt| documents/Greg Silber_reviews.txt|
| 7 | Rate My Professor website| John Aromando.txt| documents/John Aromando.txt|
| 8 | Rate My Professor website| Katherine Wassil_review.txt| documents/Katherine Wassil_review.txt|
| 9 | Rate My Professor website| Keith Decker.txt| documents/Keith Decker.txt|
| 10 | Rate My Professor website| Matthew Saponaro.txt| documents/Matthew Saponaro.txt|

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 300 characters

**Overlap:** 50 characters

**Why these choices fit your documents:**
My documents are short student reviews, typically 2–5 sentences each. At 300 characters, most individual reviews fit within a single chunk, preserving the complete opinion without merging unrelated reviews from different students together. If I had used larger chunks (800+ characters), multiple unrelated reviews would merge into one chunk, making retrieval return unfocused results that mix different students' opinions. If I had used smaller chunks (100 characters), each chunk would be a fragment with no standalone meaning, making semantic similarity search unreliable. The 50-character overlap ensures that any sentence falling at a chunk boundary still appears in full in at least one of the two adjacent chunks, so retrieval can find the complete thought even when it straddles a boundary.

Each document was cleaned to remove extra whitespace, collapse multiple blank lines into one, and replace HTML entities such as `&amp;`, `&nbsp;`, and `&#39;`. Navigation text, boilerplate lines, and share/report buttons were also removed using pattern matching.


**Final chunk count:** 175 chunks

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (runs locally, no API key required, 384-dimensional embeddings)

**Production tradeoff reflection:**
For this development project, `all-MiniLM-L6-v2` was the right choice because it runs entirely locally with no API costs, no rate limits, and fast inference. However, for a real production deployment serving many users, I would weigh the following tradeoffs:

- **Context length:** `all-MiniLM-L6-v2` has a 256-token maximum input length, which is fine for short reviews but would be limiting for longer documents like syllabi. I would consider `text-embedding-3-small` from OpenAI which supports up to 8,191 tokens.
- **Cost:** Local models have zero per-call cost. OpenAI's embedding API costs approximately $0.02 per 1 million tokens, which matters at scale with many concurrent users.
- **Multilingual support:** If students write reviews in languages other than English, I would switch to `paraphrase-multilingual-MiniLM-L12-v2` which supports 50+ languages.
- **Accuracy on domain-specific text:** A general-purpose model may not capture academic review vocabulary as precisely as a model fine-tuned on student feedback text. For production I would evaluate fine-tuned alternatives.
- **Latency:** The local model adds approximately 50ms on CPU. An API-hosted model adds network roundtrip time but may offer GPU acceleration for faster batch processing.


---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**
The system prompt contains these explicit hard rules passed to the LLM on every request:

-> "You MUST answer ONLY using the information contained in the documents provided to you in each message. 
-> Do NOT use your general training knowledge about professors, universities, courses, or any other topic under any Circumstances. 
-> If the provided documents do not contain enough information to answer the question, you MUST respond with exactly: 'I don't have enough information in my documents to answer that."

The words ONLY and MUST NOT are used deliberately, not "try to" or "prefer to", making grounding a hard rule rather than a suggestion.

**How source attribution is surfaced in the response:**
Source attribution is guaranteed at two levels. First, the Python code in `query.py` programmatically collects unique source filenames from the retrieved chunks before the LLM is even called  this list is always accurate regardless of what the LLM says. Second, the system prompt instructs the LLM to end every response with a "Sources:" section listing the document filenames. The retrieved chunks are passed to the LLM labeled with their source filename like `[From Adarsh Sethi.txt]:` so the model can reference them correctly.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Prof. Sethi's attendance and lecture slides?| Students strongly recommend attending class even though Sethi posts his annotated slides and lecture videos online, because he adds extra information during class that is not captured in the slides. There are also in-class assignments that count toward your grade, making attendance important.| Students say that Prof. Sethi adds a lot of information during class that you can't get from the slides, and they recommend attending class even though the lectures are put up. One student stated, "ATTEND CLASS, even through he puts the lectures up, he adds a lot of info during class that you cant get from the slides." However, another criticism is that "Reading off slides, no projects or anything else really makes course boring." | Relevant| Accurate|
| 2 | What do students say about Prof. Roosen's lectures and how to succeed in his class?| Students say Roosen's lectures can be tangential and feel loaded with unnecessary information, and that most learning comes from the assigned readings (Perusalls). To succeed, students recommend doing the readings, attending class, starting projects early, and staying on top of assignments.| Students have mixed opinions about Prof. Roosen's lectures. One student stated that his lectures were "boring" and that if you don't pay attention, you'll struggle. Another student mentioned that Roosen "does go on a bit of tangents, but those tangents are interesting." To succeed in his class, students suggest that you need to "show up, practice the concepts and do the homework." It's also mentioned that if you can pay attention and stay on top of the work, you'll be "alright," especially since the class is "unavoidable" for CISC majors. However, some students have criticized Prof. Roosen's teaching style, stating that his grading scale is "odd" and that he can be "rude" and unhelpful. One student advised others to "not take this guy" due to these issues.| Relevant| Partially Accurate|
| 3 | What do students say about asking Prof. Bart questions in class or office hours?| Students consistently report that Prof. Bart is condescending and dismissive when asked questions, making the classroom feel intimidating. Most students recommend going to the TAs instead for actual help| Students say that when asking Prof. Bart questions in class or office hours, he can be "dismissive", "condescending", and "arrogant". They feel that he acts "hostile" to students who ask questions, making them feel "scared to ask any questions in fear he will not like your question". It is recommended to ask a TA or a classmate for help instead of asking Prof. Bart directly.| Relevant| Accurate|
| 4 | Wassil's class self-taught or does she teach during lectures| Mostly self-taught. Multiple students say lectures are not very helpful and that most learning happens through homework and online materials outside of class. However, Wassil herself is very accessible, kind, and willing to help during office hours.| According to the documents, Katherine Wassil's class is "pretty much self study" and the lectures cover "random topics that are unlikely to appear on exams." One student mentioned that they "hated sitting in the lectures" and stopped attending, implying that the lectures are not essential to learning the material. However, another student stated that "Prof. Wassil is great at teaching computer science" and that she is "super accessible in answering questions," suggesting that she is available to help students outside of lectures.| Relevant| Accurate|
| 5 | What is Prof. Silber's workload and grading style like| Workload is light typically 2 exams, a few programming projects, and some homework graded on effort rather than correctness. Silber allows cheat sheets on exams and is known to round up grades. Students say it is manageable even with minimal prior experience.| According to the documents, Prof. Silber's workload is considered low, with 2 exams, 1 coding assignment, and 4 homeworks. The homework is "moreso graded on effort than correctness." One student mentioned that the exams and homework assignments "were all pretty easy and didn't take much time." Additionally, Prof. Silber is willing to round up grades, as one student mentioned they received an A after being "off by 0.1%."| Relevant| Partially Accurate|

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** What do students say about Prof. Roosen's lectures and how to succeed in his class?

**What the system returned:** Students have mixed opinions about Prof. Roosen's lectures. One student stated that his lectures were "boring" and that if you don't pay attention, you'll struggle. Another student mentioned that Roosen "does go on a bit of tangents, but those tangents are interesting." To succeed in his class, students suggest that you need to "show up, practice the concepts and do the homework." It's also mentioned that if you can pay attention and stay on top of the work, you'll be "alright," especially since the class is "unavoidable" for CISC majors. However, some students have criticized Prof. Roosen's teaching style, stating that his grading scale is "odd" and that he can be "rude" and unhelpful. One student advised others to "not take this guy" due to these issues.

**Root cause (tied to a specific pipeline stage):** 
This is a chunking boundary failure in `ingest.py`. The review text that explicitly mentions Perusalls as the primary learning source. "Most of the learning will be done in the perusalls, quizzes, and assignments" was split across a chunk boundary during the chunking stage. The chunk containing this sentence began mid-sentence as a fragment, which reduced its semantic signal strength when embedded. When the embedding model in `embed.py` encoded that fragment, it did not carry enough meaning to rank highly against the query "how to succeed in his class." The retrieval stage in `retrieve.py` therefore returned other Roosen chunks that had stronger overall similarity to the query but lacked this specific detail about Perusalls.

**What you would change to fix it:**
Increasing the overlap from 50 to 100 characters in `ingest.py` would reduce the chance of a key sentence being split without appearing in full in at least one adjacent chunk. Alternatively, chunking by paragraph instead of fixed character count would keep the Perusalls sentence together with its surrounding context, making it retrievable as a complete thought rather than a fragment.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**  
Writing the Chunking Strategy section of planning.md before writing any code forced me to think concretely about my document structure before touching the pipeline. When I read my actual review files, I confirmed that 300-character chunks were the right size because most individual reviews fit within one chunk, preserving the complete student opinion without merging unrelated reviews together. Without the spec I would likely have used a default chunk size of 500 or 1000 characters, which would have merged multiple unrelated reviews into one chunk and made retrieval return unfocused results mixing different students opinions about different topics.


**One way your implementation diverged from the spec, and why:**   
My planning.md specified top-k=5 for retrieval and I kept that value. However, I did not anticipate that ChromaDB would always return 5 results even for completely out-of-scope queries like "What is the best restaurant in Paris?" meaning the Retrieved From field always shows source filenames even when the system correctly refuses to answer. The spec assumed that irrelevant queries would return no sources, but ChromaDB always returns the closest matches it has regardless of how relevant they actually are. I kept this behavior and documented it honestly rather than artificially filtering it out, because the refusal response itself is correct and the presence of source filenames in the Retrieved From box does not affect the accuracy of the answer.
---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* I gave Claude my Documents section and Chunking Strategy section from planning.md and asked it to implement `ingest.py` with a `chunk_text()` function using 300-character chunks and 50-character overlap, using only standard Python libraries with no LangChain dependency.
- *What it produced:* Claude generated a complete four-stage pipeline with separate functions for loading, cleaning, chunking, and verification. It included HTML entity decoding, boilerplate pattern removal, a chunk size warning if the total fell outside the 50 to 2000 range, and a random sample printer for inspecting chunks before embedding
- *What I changed or overrode:*  The generated cleaning function included removal patterns for Rate My Professors metadata lines like "For credit: Yes" and "Would take again: Yes" which did not appear in my documents because I had copied only the review text manually. I verified these patterns were harmless by printing and reading a full cleaned document before proceeding, and kept them as a safety net in case any metadata had slipped through.

**Instance 2**

- *What I gave the AI:*  I gave Claude my Retrieval Approach section and Architecture diagram from planning.md and asked it to write `query.py` with a system prompt that enforces grounding strictly using hard rules, and with source attribution guaranteed programmatically rather than left to the LLM to produce on its own.
- *What it produced:*   Claude generated a system prompt using strong language including ONLY and MUST NOT, and a `build_context()` function that labels each retrieved chunk with its source filename before passing it to the LLM. It also generated an `ask()` function that returns both the answer and a programmatic list of unique source filenames.
- *What I changed or overrode:*  An earlier draft of the prompt used the phrase "try to answer only from the documents" which I directed Claude to replace with "you MUST answer ONLY" because the softer language would have allowed the model to blend retrieved context with its general training knowledge. I also verified the grounding was working by testing the Paris restaurant question and confirming the system returned the refusal response rather than a plausible sounding general answer.
