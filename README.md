# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->
     The system covers community-driven, unofficial student reviews, grading trends, exam structures, and teaching styles for faculty within the Computer Science Department at Missouri State University (MSU).


     This knowledge is very important especially for CS students trying to balance heavy programming workloads with other coursework, because it is very critical to feel the gaps with the proper channels. The catalog from the official department does not relect what actuallt happens in class.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->
  | # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | r/missouristate - "Computer Science Students?"| Subreddit Thread| [https://www.reddit.com/r/missouristate/comments/i0qp21/computer_science_students/](https://www.reddit.com/r/missouristate/comments/i0qp21/computer_science_students/)|
| 2 | r/missouristate - "Computer Science at MSU"| Subreddit Thread| [https://www.reddit.com/r/missouristate/comments/jmzz5g/computer_science_at_msu/](https://www.reddit.com/r/missouristate/comments/jmzz5g/computer_science_at_msu/)|
| 3 | r/missouristate - "Will MSU be worth it for me?" (CS review)| Subreddit Thread| |[https://www.reddit.com/r/missouristate/comments/sin703/will_missouri_state_university_be_worth_it_for_me/](https://www.reddit.com/r/missouristate/comtoucments/sin703/will_missouri_state_university_be_worth_it_for_me/)
| 4 | RateMyProfessors - MSU Computer Science Faculty Index| Public Review Site| https://www.ratemyprofessors.com/search/professors/936?q=*&did=11|
| 5 | r/missouristate-Will Missouri State University be worth it for me?|Subreddit Thread | https://www.reddit.com/r/missouristate/comments/sin703/will_missouri_state_university_be_worth_it_for_me/|
| 6 | RateMyProfessors-Jamil saquel |Public Review Site |https://www.ratemyprofessors.com/professor/109481 |
| 7 | RateMyProfessors-Rahul dubey |Public Review Site |https://www.ratemyprofessors.com/professor/3092556 |
| 8 | RateMyProfessors-siming Liu |Public Review Site  |https://www.ratemyprofessors.com/professor/2593599 |
| 9 | RateMyProfessors-Hui Liu |Public Review Site | https://www.ratemyprofessors.com/professor/1071783|
| 10 | RateMyProfessors-Mukulika Ghosh| Public Review Site|https://www.ratemyprofessors.com/professor/2879300 |
---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**

**Overlap:**

**Why these choices fit your documents:**

**Final chunk count:**

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used: all-MiniLM-L6-v2 **

**Production tradeoff reflection:
all-MiniLM-L6-v2 is fast and runs locally with no API cost, making it ideal for a student project. In a real deployment, I would weigh several tradeoffs. A larger model like text-embedding-3-large (OpenAI) or instructor-xl would likely score higher on domain-specific text because it has more capacity to distinguish nuanced sentiment (e.g., "fair grader" vs. "easy grader"). However, those models introduce API latency and per-token cost. Context length is also a factor: all-MiniLM-L6-v2 has a 256-token limit, which is fine for short reviews but would truncate longer forum posts. A model with a 512- or 1024-token context window would be safer for mixed-length corpora. Multilingual support is not a concern here since all sources are in English.
**

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:
You are an unofficial guide for Computer Science students at Missouri State University (MSU).

You answer questions about CS professors, course difficulty, grading styles, exam structures, and teaching styles — based ONLY on the student reviews and Reddit comments provided to you as context.

Rules you must follow:
1. Answer using ONLY information from the provided context. Do not use any outside knowledge.
2. If the context does not contain enough information to answer the question, say: "I don't have enough reviews to answer that confidently."
3. Never invent quotes, ratings, or opinions that are not in the context.
4. Keep your answer concise and focused on what students actually said.
5. Include a Sources section or any source citations in your response."""
**

**How source attribution is surfaced in the response: it willl be displayed down as sources: **

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Rahul Dubey's exam difficulty?| The response should reflect a very good rating overall and good teaching style overall| No enoough dat so no relevant answer| good| good|
| 2 | How do students describe Mukulika Ghosh's grading style?| The response should reflect how Mukulika ghosh is not a good teacher in terms of how she teaches anfd reflect a low rating| The answer is that Gosh is considered as supper difficult | very good| very good|
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

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

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

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

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
