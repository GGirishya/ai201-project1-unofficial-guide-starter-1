# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

 The system covers community-driven, unofficial student reviews, grading trends, exam structures, and teaching styles for faculty within the Computer Science Department at Missouri State University (MSU).


     This knowledge is very important especially for CS students trying to balance heavy programming workloads with other coursework, because it is very critical to feel the gaps with the proper channels. The catalog from the official department does not relect what actuallt happens in class.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

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

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->
     <!-- I will use a 200 words chunk size and a 20 words overlap -->

**Chunk size:200 characters**

**Overlap:20 characters**

**Reasoning: 

     Both RateMyProfessors and Reddit comments and reviews are naturally short, most are sentences or two expressing a single opinion maybe teaching style. 200 characters as chunks preserve one coherent thought per chunk. Big chunk would merge unrelated opinions from different reviewers into one chunk, which would merge unrelated opinions, not that it will not happen. I made the overlap to be 20 characters becayse then if by mistake the chunk is cut off then we have a chance to amend the prcess
**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model: all-MiniLM-L6-v2 **

**Top-k: 3 **

**Production tradeoff reflection: 
     all-MiniLM-L6-v2 is fast and runs locally with no API cost, making it ideal for a student project. In a real deployment, I would weigh several tradeoffs. A larger model like text-embedding-3-large (OpenAI) or instructor-xl would likely score higher on domain-specific text because it has more capacity to distinguish nuanced sentiment (e.g., "fair grader" vs. "easy grader"). However, those models introduce API latency and per-token cost. Context length is also a factor: all-MiniLM-L6-v2 has a 256-token limit, which is fine for short reviews but would truncate longer forum posts. A model with a 512- or 1024-token context window would be safer for mixed-length corpora. Multilingual support is not a concern here since all sources are in English.

**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about Rahul Dubey's exam difficulty?| The response should reflect a very good rating overall and good teaching style overall|
| 2 | How do students describe Mukulika Ghosh's grading style?| The response should reflect how Mukulika ghosh is not a good teacher in terms of how she teaches anfd reflect a low rating|
| 3 | What do MSU CS students say about the overall difficulty of the CS program?| The response should be moderate because most of the things in the document would reflect the good and the bad but the program being affordable should be very and the very first thing to point out|
| 4 | Is Hui Liu recommended by students, and what reasons do they give?| With more than 28 rating the response should reflect that there's a high difficulty in the classes especially since they are high level classes to begiin with|
| 5 | What do students say about the teaching style of Siming Liu?| The response should be more about |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. There is not enough data to use, one because i could not find it also because there is not enough reviews online about our school's program.

2.There might be a lot of halucinations since the chunks are 200 char with the overlap of 20, we can always anticipate halucinations.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

     ```
┌─────────────────────────────────────────────────────────────────────┐
│  1. DOCUMENT INGESTION                                              │
│     Tool: Python (requests + praw for Reddit, manual HTML save      │
│           for RateMyProfessors)                                     │
│     Output: raw .txt files per source, saved to documents/          │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  2. CHUNKING                                                        │
│     Tool: Python (custom chunk_text() function)                     │
│     Chunk size: 200 chars | Overlap: 20 chars                       │
│     Output: list of (chunk_text, metadata) tuples                   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  3. EMBEDDING + VECTOR STORE                                        │
│     Embedding model: all-MiniLM-L6-v2 (sentence-transformers)       │
│     Vector store: ChromaDB (local, persistent)                      │
│     Output: embedded chunks stored in chroma collection             │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  4. RETRIEVAL                                                       │
│     Tool: ChromaDB .query()                                         │
│     Top-k: 3 most similar chunks per user query                     │
│     Output: top-3 chunk texts + source metadata                     │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  5. GENERATION                                                      │
│     Model: llama-3.3-70b-versatile via Groq API                     │
│     Input: system prompt + retrieved chunks + user query            │
│     Interface: Gradio                                               │
│     Output: grounded natural language answer with source citations  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement certain methods.

     I also ended up using AI to help me format some data as txt because i could not scrape data directly from reddit.
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
   <!--- I intend to provide all the strategy and thoughts i have to claude and gemini and see what the results are
     hopefully get to learn why the implementation i have might be flawed or naive then get to learn better ways of 
     implementing these methods. -->

**Milestone 4 — Embedding and retrieval:

**

**Milestone 5 — Generation and interface:**
