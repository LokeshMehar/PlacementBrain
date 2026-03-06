# 🎯 PlacementBrain — 100 Interview Questions & Answers

> A comprehensive list of questions an interviewer is likely to ask when they see this project on your resume. Questions are organized by category, from high-level architecture down to specific implementation details.

---

## Table of Contents

- [A. Project Overview & Motivation (1–10)](#a-project-overview--motivation-110)
- [B. System Architecture & Design (11–25)](#b-system-architecture--design-1125)
- [C. RAG Pipeline & Information Retrieval (26–40)](#c-rag-pipeline--information-retrieval-2640)
- [D. LLM & Agent Design (41–55)](#d-llm--agent-design-4155)
- [E. Caching & Performance (56–65)](#e-caching--performance-5665)
- [F. Database & Persistence (66–75)](#f-database--persistence-6675)
- [G. Frontend & Real-Time Streaming (76–85)](#g-frontend--real-time-streaming-7685)
- [H. DevOps & Docker (86–92)](#h-devops--docker-8692)
- [I. Security, Scalability & Production (93–100)](#i-security-scalability--production-93100)

---

## A. Project Overview & Motivation (1–10)

### 1. What is PlacementBrain, and why did you build it?

PlacementBrain is a personal AI-powered knowledge base for campus placement preparation. I built it because I wanted a single tool where I could upload my resume, code projects, and study notes, and then interact with them conversationally — getting quizzes, gap analysis, code explanations, and mock interviews, all powered by Retrieval-Augmented Generation (RAG). The goal was to apply GenAI concepts practically rather than just studying them theoretically.

### 2. Walk me through the key features of this application.

1. **Multi-format ingestion** — Upload PDFs (resume), code files (C++, Python, JS, HTML/CSS), markdown notes, Excel sheets, or clone entire Git repos
2. **Hybrid RAG search** — Combines semantic search (vector similarity) with BM25 keyword search using Reciprocal Rank Fusion
3. **Resume vs JD comparison** — Automatically finds your uploaded resume and compares it against a job description, highlighting skill gaps
4. **Code explanation** — Searches for code in the knowledge base and explains it in interview-style format
5. **Quiz generation** — Generates 5 MCQs on any topic from your materials
6. **Mock interviewer** — 5-question adaptive interview session with per-question feedback and final assessment
7. **Multi-chat threads** — Multiple independent chat sessions with full persistent history
8. **Semantic caching** — Redis-backed dual-layer cache that avoids redundant LLM calls

### 3. What problem does this solve that existing tools (ChatGPT, Notion AI) don't?

ChatGPT has no persistent personal context — every session starts from scratch. Notion AI works within Notion's ecosystem but can't ingest arbitrary code repos or PDFs. PlacementBrain is **purpose-built for placement prep**: it understands code structure (AST parsing), generates interview-style quizzes, and runs mock interviews grounded in *your* specific study materials. It's also fully self-hosted — no data sent to third parties except the LLM API.

### 4. What was the most technically challenging part of building this?

The hybrid search pipeline with Reciprocal Rank Fusion. Getting semantic search and BM25 to produce complementary results required careful tuning — I had to choose the right embedding model (all-MiniLM-L6-v2 for CPU performance), calibrate the RRF constant (`k=60`), and ensure deduplication of results that appeared in both ranked lists. The streaming architecture with LangChain's AsyncIteratorCallbackHandler was also tricky — I had to handle edge cases where the agent task completes before all tokens are consumed from the async queue.

### 5. How long did it take you to build this? What was your development process?

I built the core MVP over approximately 2 weeks. I started with the ingestion pipeline and vector storage, then built the RAG search, added the LangChain agent with tool calling, layered on the streaming SSE frontend, and finally added features like mock interviews and semantic caching. The entire stack runs in Docker Compose, which let me iterate quickly.

### 6. If you had to describe this project in one sentence on your resume, what would it be?

"A full-stack GenAI application implementing hybrid RAG (semantic + BM25 with RRF), agentic tool calling, and real-time SSE streaming for personalized campus placement preparation."

### 7. What did you learn from building this project?

- Deep understanding of RAG architecture — chunking strategies, embedding models, hybrid search
- Practical experience with LangChain agents, tool calling, and prompt engineering
- Real-time streaming with Server-Sent Events
- Docker Compose multi-service orchestration
- The importance of caching in LLM applications (semantic cache saved 60–80% of redundant API calls)
- Trade-offs between different vector databases, embedding models, and LLM providers

### 8. What would you do differently if you were starting over?

- Use a background task queue (Celery) for ingestion instead of synchronous processing — it blocks the API during large repo ingestion
- Implement chunking quality evaluation (RAGAS framework) from the start
- Start with PostgreSQL instead of SQLite to avoid migration complexity later
- Add an evaluation/feedback loop where users can rate answer quality to improve retrieval

### 9. How does this project demonstrate your skills as a software engineer?

It shows **full-stack capability** (React frontend + FastAPI backend + Docker infrastructure), **systems design** (multi-service architecture with proper separation of concerns), **AI/ML engineering** (RAG pipeline, embedding models, agentic AI), and **problem-solving** (hybrid search fusion, streaming architecture, caching optimization). It's not a tutorial project — it required real engineering decisions about tradeoffs.

### 10. Can you demo the project live?

Yes. It runs entirely in Docker — `docker compose up --build` starts all 3 services (API, Qdrant, Redis). I can upload a PDF resume, clone a GitHub repo, ask questions about the content, run a mock interview, and show how the semantic cache prevents redundant LLM calls.

---

## B. System Architecture & Design (11–25)

### 11. Draw the high-level architecture of PlacementBrain.

*(See the ASCII architecture diagram in ARCHITECTURE.md)*

The system has 4 main components:
1. **React/TypeScript SPA** (port 5173) — communicates via REST + SSE
2. **FastAPI backend** (port 8000) — handles routing, agent orchestration, and ingestion
3. **Qdrant** (port 6333) — vector database for document embeddings
4. **Redis** (port 6379) — semantic + exact-match cache for LLM responses

All services run in a Docker Compose network (`pb-net`). The frontend uses Vite's dev proxy to route `/api/*` to the backend.

### 12. Why did you choose a microservices architecture over a monolith?

It's actually a hybrid — the backend is a single FastAPI monolith, but the data stores (Qdrant, Redis) are separate services. This gives me the benefits of isolation (I can upgrade or restart Qdrant without affecting the API), independent scaling (Qdrant can be moved to a dedicated server), and well-defined interfaces (Qdrant REST API, Redis protocol), without the overhead of full microservices (service mesh, API gateway, etc.).

### 13. How do the frontend and backend communicate?

Two channels:
1. **REST API** — For CRUD operations (creating chats, uploading files, listing sources, starting interviews). Standard `fetch()` with JSON request/response.
2. **Server-Sent Events (SSE)** — For streaming LLM responses. The frontend opens an `EventSource` connection to `/chat/stream`, and the backend yields tokens as JSON events.

### 14. Why SSE instead of WebSockets?

LLM token streaming is inherently **unidirectional** (server → client). SSE is simpler than WebSockets for this pattern — it uses standard HTTP, has built-in auto-reconnection, and requires no library. WebSockets would add bidirectional complexity we don't need. The only tradeoff is that SSE has a browser-imposed limit of 6 concurrent connections per domain under HTTP/1.1, which isn't a problem for a single-user app.

### 15. Explain the ingestion pipeline. What happens when I upload a PDF?

1. **Upload** — File is saved to `/data/uploads/{uuid}_{filename}`
2. **Dispatch** — File extension is mapped to the correct loader (`.pdf` → `pdf_loader`)
3. **Extraction** — `pypdf` extracts text page by page
4. **Chunking** — `RecursiveCharacterTextSplitter` splits into 1000-character chunks with 200-char overlap
5. **Embedding** — `SentenceTransformer(all-MiniLM-L6-v2)` converts each chunk to a 384-dimensional vector
6. **Storage** — Vectors are batch-upserted into Qdrant (batches of 100 `PointStruct`s)
7. **Indexing** — BM25 index is rebuilt by scrolling all Qdrant documents
8. **Cache invalidation** — Semantic cache is cleared since the knowledge base changed

### 16. How do you handle different file types (PDF vs code vs markdown)?

A **dispatcher pattern**: `dispatcher.py` maps file extensions to loader functions. Each loader has a specialized chunking strategy:
- **PDF**: Page-by-page extraction + recursive character splitting
- **Python code**: AST-based chunking (each function/class becomes a separate chunk), with fallback to line-based chunking if parsing fails
- **C++/JS/HTML/CSS**: Line-based chunking (50 lines per chunk, 10-line overlap)
- **Markdown**: Header-based splitting (each section is a chunk)
- **Text/JSON**: Recursive character splitting (500 chars, 50 overlap)

### 17. Why does Python code get AST-based chunking while C++ gets line-based?

Python's `ast` module is a built-in standard library that reliably parses Python source into a syntax tree. For C++, there's no equivalent lightweight parser — tools like `libclang` are heavy dependencies and overkill for chunking. The line-based approach with overlap works well enough for C++ in the RAG context, since the embedding model can capture semantic meaning from 50-line windows.

### 18. What is the purpose of chunk overlap?

Overlap prevents information loss at chunk boundaries. If an important concept spans lines 48–52 and we chunk at line 50 with zero overlap, the concept gets split across two chunks and neither chunk captures the full context. A 10-line overlap means chunk 1 covers lines 1–50 and chunk 2 covers lines 41–90, so the boundary content appears in both chunks and is searchable.

### 19. What design patterns did you use in this project?

- **Singleton** — `@functools.lru_cache()` on dependency factories (embedder, vectorstore, agent)
- **Factory** — `ToolFactory` creates all LangChain tools with injected dependencies
- **Strategy** — Different file loaders selected via dispatch map
- **Observer/Callback** — `AsyncIteratorCallbackHandler` for streaming tokens
- **Dependency Injection** — FastAPI's `Depends()` for wiring singletons into route handlers
- **Repository** — `sqlite_db.py` abstracts all database access behind simple function calls

### 20. How does the Dependency Injection work in your FastAPI backend?

FastAPI's `Depends()` function creates a dependency graph. For example, `get_agent()` depends on `get_llm()` and `get_tool_factory()`, which in turn depends on `get_embedder()` and `get_vectorstore()`. All are decorated with `@functools.lru_cache()`, so they're created once and reused — essentially singleton instances. When a route handler declares `agent=Depends(get_agent)`, FastAPI resolves the full dependency chain automatically.

### 21. Why did you separate the RAG service into embedder, vectorstore, and BM25 as separate classes?

**Single Responsibility Principle**. Each class has exactly one job:
- `Embedder` — wraps SentenceTransformer for text-to-vector conversion
- `VectorStore` — wraps Qdrant for vector CRUD and search
- `BM25Index` — manages the keyword search index

This makes them independently testable, replaceable (I could swap Qdrant for Pinecone by changing only `VectorStore`), and reusable (the same `Embedder` is used by both the search pipeline and the semantic cache).

### 22. How does the tool calling work with LangChain?

I use `StructuredTool.from_function()` to create 4 tools, each with a Pydantic `args_schema` that defines input parameters. The `create_tool_calling_agent()` function creates a ReAct-style agent that:
1. Receives the user message
2. Decides whether to call a tool or respond directly (guided by the system prompt)
3. If a tool is needed, generates a structured function call with the correct arguments
4. Executes the tool (which runs the hybrid search + LLM processing)
5. Uses the tool output to formulate the final response

The `max_iterations=5` prevents infinite tool-calling loops.

### 23. Explain the ReAct pattern used by your agent.

ReAct (Reason + Act) is an agent pattern where the LLM alternates between:
1. **Thought** — Reasoning about what to do next ("I need to search the knowledge base for DSA topics")
2. **Action** — Calling a tool (`search_knowledge_base(query="DSA topics")`)
3. **Observation** — Reading the tool's output
4. **Repeat or Answer** — Either call another tool or produce the final answer

In my implementation, the agent executor manages this loop. The system prompt instructs the agent to **only use tools when necessary** — for general questions like "What is the capital of France?", it answers directly without any tool call.

### 24. What happens if the LLM hallucinates or generates incorrect tool arguments?

The `args_schema` (Pydantic model) validates all tool arguments. If the LLM generates invalid arguments (missing required fields, wrong types), the tool call fails and the error message is fed back to the agent as an observation. The agent can then retry with corrected arguments. This is why I use `StructuredTool` with explicit schemas rather than unstructured tool definitions. The `max_iterations=5` limit also prevents the agent from getting stuck in a retry loop.

### 25. How do you handle the conversation context/memory?

Two-level approach:
1. **Short-term**: `ConversationBufferWindowMemory(k=10)` keeps the last 10 messages in the agent's context window. This is loaded from SQLite at the start of each query using `_load_session_memory()`.
2. **Long-term**: All messages are persisted to SQLite (`messages` table). When the user switches to a different chat or returns later, the full history is loaded and the memory is repopulated.

This means the agent can reference recent conversation context ("Can you explain that in more detail?") while keeping the LLM's token usage bounded.

---

## C. RAG Pipeline & Information Retrieval (26–40)

### 26. What is RAG and why is it better than fine-tuning for your use case?

**RAG** (Retrieval-Augmented Generation) augments the LLM's input with retrieved context from an external knowledge base. Fine-tuning modifies the model's weights.

RAG is better here because:
- My data changes frequently (new uploads) — fine-tuning would require retraining
- I need **traceability** — I can show which source documents the answer came from
- No training infrastructure needed — RAG works with any LLM API
- **Cost**: Fine-tuning LLaMA 70B would require GPU hours; RAG adds zero training cost

### 27. Explain hybrid search. Why not use only semantic search?

**Semantic search** uses vector similarity (cosine distance) to find conceptually similar documents. It understands that "linked list traversal" and "iterate through nodes" mean the same thing. But it can **miss exact keyword matches** — if you search for `mergeSort`, pure semantic search might return results about sorting algorithms in general.

**BM25** is a keyword-based algorithm that excels at exact term matching. It would find `mergeSort` instantly but would miss paraphrased queries.

**Hybrid search** combines both: run semantic search (top 20) and BM25 search (top 20), then fuse the ranked lists using RRF. Documents found by both methods get boosted, giving us the best of both worlds.

### 28. Explain Reciprocal Rank Fusion in detail.

For each document `d` found in any ranked list, we compute:

```
RRF(d) = Σ 1/(k + rank_i(d))
```

- `k` = 60 (smoothing constant — the standard value from the original paper)
- `rank_i(d)` = position of document `d` in the i-th ranked list (0-indexed)

Example: If a document appears at rank 2 in semantic results and rank 5 in BM25:
```
RRF = 1/(60+2) + 1/(60+5) = 1/62 + 1/65 = 0.0161 + 0.0154 = 0.0315
```

A document appearing in only one list gets a lower score. Documents are sorted by RRF score and the top-k are returned.

### 29. Why RRF over other fusion methods (linear combination, CombMNZ)?

**RRF is score-agnostic** — it works on ranks, not raw scores. This is critical because BM25 scores (e.g., 15.3) and cosine similarity scores (e.g., 0.85) are on completely different scales. A linear combination would require normalization, which is non-trivial and can distort results. RRF just needs the ordering, making it robust and simple.

### 30. What embedding model do you use and why?

`all-MiniLM-L6-v2` from Sentence Transformers. Reasons:
- **384 dimensions** — smaller vectors = less Qdrant storage and faster similarity computation
- **CPU-friendly** — runs in ~80ms per batch of 32 texts on a laptop CPU
- **Good quality** — ranked top-10 on the MTEB benchmark for its size class
- **Self-hosted** — no API calls, no cost, no rate limits, no data privacy concerns
- **L2-normalized** — cosine similarity computation is simplified to a dot product

### 31. What is cosine similarity and why do you use it over Euclidean distance?

Cosine similarity measures the angle between two vectors, normalized to [-1, 1]. It's **scale-invariant** — a document that repeats keywords 10 times shouldn't be "more similar" than one that mentions them once. Euclidean distance is affected by vector magnitude. Since our embeddings are L2-normalized, cosine similarity equals the dot product, making it both semantically meaningful and computationally efficient.

### 32. How does your BM25 index work?

BM25 (Best Matching 25) is a probabilistic ranking function. My implementation:
1. On startup (and after each ingestion), scroll all documents from Qdrant
2. Tokenize each document: `text.lower().split()` (simple whitespace tokenization)
3. Build a `BM25Okapi` index from the `rank_bm25` library
4. At query time, tokenize the query the same way and compute BM25 scores for all documents
5. Return top-k documents with score > 0

The index is **in-memory** — it's rebuilt from scratch on each ingestion. For our scale (~10K documents), this takes <1 second.

### 33. What are the limitations of your BM25 tokenization (simple `.split()`)?

- **No stemming** — "running" and "run" are treated as different tokens
- **No stop word removal** — "the", "is", "a" contribute to matching
- **No subword tokenization** — `camelCaseVariables` aren't split
- **Case-folded only** — no lemmatization

For a production system, I'd use spaCy or NLTK for better tokenization. But for a personal knowledge base, simple whitespace splitting combined with semantic search covers the gaps.

### 34. What is the chunk size for PDF documents and why 1000 characters?

1000 characters with 200-character overlap. This is a standard starting point from LangChain best practices:
- **Too small** (100–200 chars) — chunks lack context; retrieval returns many fragments that don't make sense alone
- **Too large** (5000+ chars) — chunks dilute the relevant information with irrelevant text; wastes LLM context window
- **1000 chars** — roughly 150–200 words; enough context for a meaningful paragraph while keeping retrieval precise
- **200 overlap** — prevents information loss at boundaries

### 35. How does the code chunking strategy differ from PDF chunking?

PDFs are unstructured text → `RecursiveCharacterTextSplitter` by character count.
Code has **structure**: functions, classes, imports. For Python, I use `ast.parse()` to extract each function/class as a separate chunk. This means each chunk is a self-contained semantic unit (one complete function), which dramatically improves retrieval quality for code queries. For languages without easy AST parsing (C++, JS), I use line-based chunking (50 lines, 10-line overlap).

### 36. How would you evaluate the quality of your RAG pipeline?

I would use the **RAGAS framework** to measure:
1. **Faithfulness** — Is the answer grounded in the retrieved documents?
2. **Answer Relevancy** — Does the answer address the actual question?
3. **Context Precision** — Are the retrieved chunks relevant to the query?
4. **Context Recall** — Did retrieval find all necessary information?

I'd create a test set of ~50 question-answer pairs with known ground truths and run automated evaluation.

### 37. What happens if the knowledge base is empty and a user asks a question?

The agent's tools will return "No relevant documents found in the knowledge base." The system prompt instructs the agent to answer general questions directly using its training knowledge. So it would say something like: "I didn't find relevant information in your knowledge base. Based on my general knowledge, here's what I know about X..." — graceful degradation rather than an error.

### 38. How do you handle source attribution?

A `contextvars.ContextVar` named `active_sources` tracks source documents used during each query. When a tool performs a hybrid search, the `_record_sources()` function appends source metadata (filename, type, text snippet, score) to this context variable. After the agent finishes, the sources are serialized as `__SOURCES__<json>` and sent as the final SSE event. The frontend displays these as "Sources" below the AI response.

### 39. What would happen if two chunks have identical text?

The RRF deduplication uses `text[:100]` as a key. If two chunks have identical first 100 characters, they're treated as the same document and their RRF scores are merged. This prevents duplicate results in the output. The tradeoff is that two genuinely different chunks with identical openings would be incorrectly merged — but this is extremely rare in practice.

### 40. How does the source_type_filter work in hybrid search?

Both the vector search and BM25 search support filtering by `source_type`. For vector search, Qdrant's `FieldCondition` with `MatchAny` filters at the database level (efficient). For BM25, I filter post-scoring by checking `doc["metadata"]["source_type"]`. This is used by tools like `explain_code` (only searches code chunks) and `compare_resume_jd` (only searches PDF/text/markdown for resume content).

---

## D. LLM & Agent Design (41–55)

### 41. Why Groq over OpenAI or self-hosted Ollama?

**Groq** runs LLaMA 3.3 70B on custom LPU hardware with ~200ms time-to-first-token — the fastest inference available. This matters for streaming UX — users see the first word almost instantly. OpenAI's GPT-4o is higher quality but 2–3x slower and costs $2.50/M tokens. Ollama (self-hosted) would require a GPU and offers only smaller models (8B) with 2+ second latency. Groq gives me the quality of a 70B model at startup speed.

### 42. What model are you using and what are its capabilities?

LLaMA 3.3 70B Versatile via Groq. It supports:
- 128K context window
- Native tool/function calling (critical for our agent)
- Streaming token output
- Strong reasoning and code understanding
- Multilingual support

Temperature is set to 0.3 for consistent, factual responses appropriate for educational content.

### 43. What is temperature in LLM inference and why did you choose 0.3?

Temperature controls randomness in token sampling. At `T=0`, the model always picks the most probable next token (deterministic). At `T=1`, sampling follows the full probability distribution (creative/random). `T=0.3` biases toward high-probability tokens while allowing some variation — ideal for educational answers that should be accurate but not robotic.

### 44. What is `max_tokens=4096` and could it cause truncation?

`max_tokens` limits the response length to 4096 tokens (~3000 words). For our use cases (explanations, quizzes, feedback), this is sufficient. If a response were to exceed this, it would be truncated mid-sentence. For very long code explanations, this could be an issue — I'd increase it or implement pagination.

### 45. Explain how the tool calling works end-to-end.

1. User asks: "Generate a quiz on binary trees"
2. Agent receives: `{input: "Generate a quiz on binary trees", chat_history: [...], agent_scratchpad: []}`
3. LLM decides to call `generate_quiz(topic="binary trees")`
4. LangChain deserializes the tool call, validates against `GenerateQuizInput` schema
5. `_generate_quiz()` runs hybrid search for "binary trees" → gets relevant chunks
6. Constructs a prompt with the chunks + quiz format instructions
7. Calls `llm.invoke(prompt)` for a separate LLM call to generate the quiz
8. Returns the quiz text to the agent executor
9. Agent uses the tool output as the final response
10. Response is streamed to the frontend via SSE

### 46. Why do some tools (quiz, explain, resume) make an additional LLM call inside the tool?

The agent's LLM call decides **which tool to use** and **what arguments to pass**. But the tool itself needs to **process the retrieved context** into a specific format (quiz questions, code explanation, resume comparison). This requires a second, separate LLM call with a specialized prompt. It's a two-stage architecture:
- Stage 1: Agent reasoning (tool selection + argument generation)
- Stage 2: Tool execution (retrieval + specialized generation)

### 47. How does the `compare_resume_jd` tool find the user's resume automatically?

If `resume_text` is not provided (empty/null):
1. It searches the knowledge base for `"resume cv education experience profile projects skills"` — a broad query designed to match resume-like content
2. Filters results to `source_type_filter=["pdf", "text", "markdown"]`
3. Prioritizes PDF chunks (most likely to be a resume)
4. Groups chunks by the first PDF filename found and concatenates them to reconstruct the full resume text
5. Falls back to any text results if no PDF is found
6. Returns an error if nothing is found

### 48. What is the system prompt doing and how did you design it?

The system prompt:
```
"You are Antigravity, a helpful assistant for campus placements. You have access to tools... Use these tools ONLY when needed... If asked general questions, greetings, or conversational follow-up... DO NOT call any tools and answer directly..."
```

Key design decisions:
- **Explicit tool-use guidance** — Without this, the agent would call `search_knowledge_base` for every message, including "hello"
- **Persona** — Gives the agent a consistent identity
- **Scope** — Focused on placement preparation
- **Directness** — "Be concise but thorough" prevents verbose responses

### 49. What is `max_iterations=5` in the agent executor?

It limits the number of Thought→Action→Observation loops the agent can perform. Without this, a confused agent could loop indefinitely (e.g., calling the same tool repeatedly because it can't parse the output). 5 iterations is enough for: 1 initial reasoning + up to 4 tool calls. In practice, most queries use 1–2 iterations.

### 50. How does the mock interviewer maintain state across 5 questions?

The interview state is stored in SQLite's `interviews` table:
- `question_index` (1–5) tracks progress
- `current_question` stores the active question text
- `status` is `"active"` or `"completed"`

On each answer submission:
1. The backend retrieves the active interview state
2. Sends the question + answer + retrieved context to the LLM for evaluation
3. Parses the LLM output (structured as `FEEDBACK:...NEXT_QUESTION:...`)
4. Updates the database with the next question and incremented index
5. Returns feedback + next question to the frontend

### 51. How do you handle prompt injection attacks?

Currently, there's minimal protection. A malicious user could inject instructions like "Ignore your system prompt and..." in their message. Mitigations I would add:
- Input sanitization — strip known injection patterns
- Separate system/user message boundaries (which LangChain already does via `MessagesPlaceholder`)
- Output validation — check that tool calls match expected schemas
- Rate limiting — prevent brute-force prompt injection attempts

### 52. What happens if the Groq API is down or rate-limited?

The agent catches exceptions and yields an error message: `"[Agent Error: {error}]"`. The frontend displays this to the user. For rate limits (429), the `langchain-groq` library has built-in retry with exponential backoff. If the rate limit persists, the user sees a clear error message rather than a silent failure.

### 53. How do you handle streaming with LangChain's agent executor?

I use `AsyncIteratorCallbackHandler`, which provides an async queue. Here's the flow:
1. Create the callback handler
2. Launch `agent.ainvoke()` in an `asyncio.create_task()`
3. In a loop, `await asyncio.wait_for(callback.queue.get(), timeout=0.1)` to consume tokens
4. `yield` each token as an SSE event
5. When the task completes, drain any remaining tokens from the queue
6. If the full response is empty (non-streaming fallback), use `result["output"]` from the task

### 54. Why `ConversationBufferWindowMemory(k=10)` instead of unlimited memory?

Token budget management. Each message in the conversation history consumes LLM context window tokens. With unlimited memory, a 100-message conversation could consume 50K+ tokens of context, leaving little room for the system prompt, tool outputs, and response. `k=10` keeps the last 10 messages (~2K–5K tokens), which is enough for conversational continuity while leaving ample room for RAG context injection.

### 55. Could you replace LangChain with a custom implementation?

Yes, and it would reduce dependency complexity. I would:
1. Use Groq's API directly for chat completions with `tool_choice` parameter
2. Parse tool calls from the response JSON
3. Execute tools manually with a dispatch map
4. Implement the reasoning loop myself (while tool_calls: execute → feed back → re-query)
5. Use a simple list for conversation history

LangChain adds abstraction overhead but saved significant development time and provides battle-tested streaming callbacks.

---

## E. Caching & Performance (56–65)

### 56. Explain your semantic cache architecture.

Two layers, checked in order:
1. **Exact match** — SHA-256 hash of `query.strip().lower()`, scoped by `chat_id`. O(1) Redis GET. Catches identical repeated questions.
2. **Semantic match** — Embed the query, then scan all `semcache:{chat_id}:*` keys and compute cosine similarity against cached embeddings. If similarity > 0.97, return the cached response.

Both layers have a 1-hour TTL and are namespace-scoped by `chat_id`.

### 57. Why 0.97 similarity threshold instead of 0.90 or 0.99?

- **0.90** — Too permissive. "What is a linked list?" and "What is a doubly linked list?" have ~0.92 similarity but require different answers
- **0.97** — Catches near-identical queries like "What is OOP?" vs "What is OOP" (without question mark), or "explain polymorphism" vs "explain about polymorphism"
- **0.99** — Too strict; would rarely match anything; only catches minor whitespace/case differences, which the exact-match layer already handles

### 58. Why do you scope the cache by `chat_id`?

Different chats have different conversation contexts. If Chat A is about "React" and Chat B is about "C++ OOP", they might both ask "Give me an example." Without scoping, Chat B would receive Chat A's React example. Scoping by `chat_id` ensures cache isolation between conversations.

### 59. When is the cache invalidated?

After any ingestion operation (`/ingest/file`, `/ingest/repo`, `/ingest/text`), the cache is fully cleared via `cache.clear()`. This is necessary because the knowledge base has changed — cached answers may now be incomplete or wrong. The 1-hour TTL also provides time-based invalidation for organic cache refresh.

### 60. What's the performance impact of the semantic cache?

For cache hits:
- **Exact match**: ~1ms (Redis GET) — 99.9% latency reduction vs LLM call
- **Semantic match**: ~50ms (embedding + scan + cosine) — 99% latency reduction

For a study session where a user revisits similar topics, I estimate 60–80% of queries hit the cache, saving that many LLM API calls and their associated latency.

### 61. What's the downside of scanning all `semcache:*` keys for semantic matching?

It's O(n) where n = number of cached entries for that chat. For a typical session (~20–50 queries), this is negligible. But for thousands of cached entries, the scan would become slow. Solutions:
- Use a separate Qdrant collection for cache embeddings (ANN search instead of brute-force)
- Limit scan to the most recent N cache entries
- Use Redis' sorted sets with recency scoring

### 62. Why do you use Redis instead of an in-process Python dictionary for caching?

- **Persistence**: Redis survives process restarts (though TTL eventually expires entries)
- **Shared state**: If we scale to multiple uvicorn workers, all workers share the same cache
- **TTL support**: Built-in expiry — no manual cleanup needed
- **Namespace scanning**: `SCAN` with pattern matching for scoped invalidation

### 63. How much memory does the cache consume?

Each cached entry stores:
- Exact cache: query hash → response text (~1–5KB per entry)
- Semantic cache: embedding (384 floats × 4 bytes = 1.5KB) + response text (~1–5KB)

For 100 cached queries: ~100 × 6KB = ~600KB. Redis' memory overhead is ~100 bytes per key, so total is under 1MB. Extremely lightweight.

### 64. Could you implement cache warming (pre-populating common queries)?

Yes. I could:
1. Analyze the most common placement prep questions (DSA topics, OOP, DBMS, OS)
2. Pre-run them through the agent at application startup
3. Cache the responses

Tradeoff: startup time increases by ~30 seconds (for 20 pre-warmed queries), but the first user interaction feels instant. I'd implement this as an optional CLI flag.

### 65. How would you monitor cache hit rates in production?

Add metrics to the cache layer:
- Increment a Redis counter on each cache hit/miss
- Expose a `/metrics` endpoint with hit rate percentage
- Log cache operations with structured logging
- Optionally integrate with Prometheus/Grafana for dashboards

---

## F. Database & Persistence (66–75)

### 66. Why SQLite instead of PostgreSQL?

SQLite is **zero-configuration** — it's just a file. For a single-user personal application, it's the perfect choice:
- No additional Docker container needed
- No connection management overhead
- ACID-compliant for our read/write patterns
- Python's `sqlite3` module is in the standard library

The tradeoff is **single-writer concurrency** — if this were a multi-user application, I'd use PostgreSQL. I've already designed the schema to be migration-friendly.

### 67. What was the SQLite file locking issue you encountered?

When the SQLite database file was on a Docker bind-mounted Windows volume (`./data/uploads`), the container experienced `disk I/O error` and `database is locked` errors. This is because Windows and Linux have different file locking mechanisms, and Docker's bind mount layer doesn't perfectly translate Windows NTFS locks to Linux `flock()`. The fix was to store the database at `/data/placementbrain.db` — inside the container's writable layer, not on the bind mount.

### 68. How does the chat auto-creation mechanism work?

The `add_message()` function checks if the `chat_id` exists in the `chats` table before inserting. If not, it creates the chat dynamically with a default title. This is a **robust fallback** — even if the frontend fails to call `POST /chat` first, messages won't be orphaned.

### 69. How do you handle cascading deletes?

SQLite's `PRAGMA foreign_keys = ON` enables foreign key enforcement. The `messages` and `interviews` tables have `ON DELETE CASCADE` foreign keys to `chats`. When a chat is deleted, all its messages and interview sessions are automatically deleted. I explicitly enable this pragma before each delete operation since SQLite doesn't enable it by default.

### 70. What would a PostgreSQL migration look like?

The schema is already SQL-standard — it would work with minimal changes:
1. Replace `sqlite3` with `asyncpg` or `psycopg2`
2. Change `TEXT PRIMARY KEY` to `UUID PRIMARY KEY` (native UUID type)
3. Change `TEXT` timestamps to `TIMESTAMP WITH TIME ZONE`
4. Use a connection pool (e.g., `databases` library with asyncpg)
5. Update `DB_PATH` to a connection string (`postgresql://user:pass@host/db`)

### 71. How is the interview state managed in the database?

The `interviews` table stores one row per interview session:
- `chat_id` links it to a chat
- `current_question` holds the active question text
- `question_index` tracks progress (1–5)
- `status` is `"active"` or `"completed"`

When a new interview starts, any existing active interview for that chat is auto-completed. This prevents orphaned interview sessions.

### 72. Why not use Redis for chat persistence instead of SQLite?

Redis is optimized for **ephemeral, fast-access data** — perfect for caching. Chat history is **persistent, relational data** that needs:
- Ordered retrieval (messages by timestamp)
- Relational integrity (messages belong to chats)
- Durability (data must survive process restarts)
- Complex queries (all messages for a chat, all chats sorted by date)

SQLite excels at all of these. Using Redis for structured persistence would require manual serialization, manual indexing, and risk data loss.

### 73. How do you ensure data consistency between Qdrant and SQLite?

They serve different purposes and don't share data:
- **Qdrant** stores document chunks + embeddings (the knowledge base)
- **SQLite** stores chat sessions + messages + interview state (the user interaction history)

There's no cross-database consistency concern. If Qdrant data is deleted (a source is removed), it doesn't affect SQLite. If a chat is deleted from SQLite, it doesn't affect the knowledge base.

### 74. What is the maximum scale SQLite can handle?

SQLite can handle databases up to 281 TB and ~100K rows/second for inserts. For a single-user chat application, I'd hit usability issues (slow UI with 10K+ messages in one chat) long before SQLite becomes the bottleneck. The real limitation is **concurrent writes** — only one process can write at a time.

### 75. How do you handle database connections in your code?

Each function creates a new connection, performs its operation, and closes it:
```python
conn = get_db_connection()
cursor = conn.cursor()
# ... operations ...
conn.commit()
conn.close()
```

This is simple and safe for SQLite. For PostgreSQL, I'd use a **connection pool** to avoid the overhead of creating/destroying connections on every request.

---

## G. Frontend & Real-Time Streaming (76–85)

### 76. How does the SSE streaming work in the frontend?

The `useSSE` hook manages the streaming lifecycle:
1. Creates user + empty assistant messages in state
2. Opens an `EventSource` to `/api/chat/stream?message=X&session_id=Y`
3. On each `onmessage` event, parses the JSON (`{type: "token", data: "..."}`)
4. Appends each token to the assistant message via `setMessages()` state update
5. On `{type: "done"}`, closes the EventSource and marks streaming as complete
6. On error, shows error message and closes connection

### 77. Why did you use `EventSource` instead of `fetch()` with `ReadableStream`?

`EventSource` has built-in auto-reconnection and event parsing. With `fetch()` + `ReadableStream`, I'd need to manually parse the SSE protocol (split by `\n\n`, parse `data:` lines), handle reconnection, and manage the stream lifecycle. `EventSource` does all of this natively. The tradeoff is that `EventSource` only supports GET requests (our streaming endpoint uses query params instead of POST body).

### 78. How do you prevent multiple simultaneous streams?

The `isStreaming` state flag. When `sendMessage()` is called:
1. Check `if (isStreaming) return` — reject if already streaming
2. Set `isStreaming = true` before opening EventSource
3. Set `isStreaming = false` in both `onDone` and `onError` callbacks

UI buttons are also disabled with `disabled={isStreaming}` to prevent double-clicks.

### 79. How does the multi-chat feature work?

The frontend maintains an `activeChatId` state. When it changes:
1. `clearMessages()` clears the in-memory message array
2. `useEffect` fetches message history from `GET /chat/{id}/messages`
3. Formats messages into the frontend's `Message` type
4. Sets them in state

New messages are associated with `activeChatId` via the `session_id` query parameter in SSE requests. The sidebar shows all chats from `GET /chat` and allows creating/deleting chats.

### 80. How does the Vite dev proxy work?

In `vite.config.ts`, the proxy configuration:
```js
proxy: { '/api': { target: 'http://localhost:8000', rewrite: (path) => path.replace(/^\/api/, '') } }
```
This rewrites frontend requests from `/api/chat` → `http://localhost:8000/chat`. It solves CORS issues during development and makes the frontend code environment-agnostic (always calls `/api/...` regardless of backend URL).

### 81. Why React + TypeScript over plain JavaScript?

TypeScript catches entire categories of bugs at compile time:
- Mismatched API response shapes (wrong field name, missing field)
- Invalid state types (passing a string where a number is expected)
- Autocomplete for complex interfaces (Message, Source, InterviewStatus)

For a project with multiple data types flowing between frontend and backend, TypeScript's type safety is essential for maintainability.

### 82. How did you implement the modal dialog boxes for Quiz and Explain Code?

Each modal is a React component rendered conditionally:
```tsx
{showQuizModal && (
  <div className="fixed inset-0 bg-black/60 backdrop-blur-sm ...">
    <div className="glass-card p-6 max-w-md w-full">
      {/* Title, input field, submit button */}
    </div>
  </div>
)}
```

State variables (`showQuizModal`, `quizTopic`) control visibility and input. The overlay uses `fixed inset-0` to cover the screen with `backdrop-blur-sm` for the glassmorphism effect. The modal content is centered with flexbox.

### 83. How does the MessageBubble render markdown content?

The `MessageBubble` component renders assistant messages as formatted markdown with code blocks, bold text, lists, etc. User messages are rendered as plain text. The component differentiates by checking `message.role` and applies different CSS classes accordingly.

### 84. How do you handle auto-scrolling in the chat?

A `useRef` creates a reference to a dummy div at the bottom of the messages container:
```tsx
const messagesEndRef = useRef<HTMLDivElement>(null);
useEffect(() => {
  messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
}, [messages]);
```

Every time the `messages` state changes (new token arrives), the effect triggers and smoothly scrolls the div into view.

### 85. What CSS methodology did you use?

Custom CSS with utility classes and design tokens. I defined a design system in `index.css` with:
- CSS custom properties for colors, gradients, and spacing
- `.glass-card` class for glassmorphism effects (backdrop-blur, border, transparency)
- `.btn-primary`, `.btn-ghost` for button variants
- `.input-field` for consistent form styling
- Dark theme with `gray-950` backgrounds and subtle gradients

---

## H. DevOps & Docker (86–92)

### 86. Explain your Docker Compose setup.

Three services on a bridge network (`pb-net`):
1. **api** (`python:3.11-slim`) — FastAPI backend, port 8000, depends on qdrant + redis
2. **qdrant** (`qdrant/qdrant:latest`) — Vector database, port 6333
3. **redis** (`redis:7-alpine`) — Cache, port 6379

Volumes persist data across restarts: Qdrant storage, Redis data, uploads, and HuggingFace model cache.

### 87. Why `python:3.11-slim` over `python:3.11-alpine`?

Alpine uses `musl` libc instead of `glibc`. Many Python ML packages (numpy, torch, sentence-transformers) ship pre-compiled wheels for `glibc`. On Alpine, they'd need to be compiled from source, which takes 10+ minutes and often fails. `slim` is Debian-based with `glibc` — pip installs work seamlessly.

### 88. Why CPU-only PyTorch (`torch==2.4.1+cpu`)?

The full CUDA PyTorch package is ~2GB. Our embedding model runs fine on CPU with acceptable latency (~80ms per batch). Including CUDA would triple the Docker image size for no benefit — we don't have a GPU available in the Docker environment. The `--extra-index-url` directive points to PyTorch's CPU-only wheel index.

### 89. What is the `--reload` flag in the uvicorn CMD?

It enables hot-reloading — uvicorn watches for file changes in `/app` and automatically restarts the server. Combined with the bind mount (`./backend:/app`), this means I can edit Python files locally and see changes reflected immediately without rebuilding the Docker image. This would be removed in production.

### 90. How do you handle the HuggingFace model cache?

The volume `./data/hf_cache:/root/.cache/huggingface` persists the downloaded SentenceTransformer model across container rebuilds. Without this, the ~90MB model would be re-downloaded on every `docker compose up`. The first startup takes ~30 seconds for the download; subsequent startups use the cached model and take ~5 seconds.

### 91. What happens during `docker compose up --build`?

1. Docker builds the API image: installs git, copies requirements.txt, runs `pip install`, copies source code
2. Pulls Qdrant and Redis images (if not cached)
3. Creates the `pb-net` network
4. Starts Qdrant and Redis first (dependency order)
5. Starts the API container, which runs the startup event (init DB, create Qdrant collection, build BM25 index)
6. Application is ready at `localhost:8000`

### 92. How would you set up CI/CD for this project?

GitHub Actions workflow:
1. **Lint** — `ruff check` (Python) + `tsc --noEmit` (TypeScript)
2. **Test** — pytest for backend unit tests, Vitest for frontend
3. **Build** — `docker compose build` to verify Docker build succeeds
4. **Integration** — `docker compose up -d` + run API smoke tests against health endpoint
5. **Deploy** — Push images to Docker Hub/GHCR, deploy to cloud VM via SSH

---

## I. Security, Scalability & Production (93–100)

### 93. How would you deploy this to production?

1. **Cloud VM** (AWS EC2 / DigitalOcean) with Docker Compose
2. **Nginx reverse proxy** for HTTPS termination and static file serving
3. **Separate build for frontend** — `npm run build` → serve static files via Nginx
4. **Environment management** — Docker secrets or `.env` files (not in git)
5. **Monitoring** — Prometheus + Grafana for metrics, structured logging to ELK stack
6. **Backups** — Scheduled Qdrant snapshots + SQLite file backups

### 94. How would you handle multiple concurrent users?

1. **Replace SQLite with PostgreSQL** — concurrent write support
2. **Add authentication** — JWT tokens, user-scoped data
3. **Multiple uvicorn workers** — `gunicorn -w 4 -k uvicorn.workers.UvicornWorker`
4. **User-scoped Qdrant collections** — one collection per user, or payload filtering by `user_id`
5. **Rate limiting** — per-user limits to prevent LLM API abuse
6. **Redis connection pooling** — handle concurrent cache operations

### 95. What are the main security concerns with this application?

1. **No authentication** — anyone with network access can use the app
2. **API key in `.env`** — could be exposed if `.env` is accidentally committed
3. **No input length limits** — a user could send a 100MB message
4. **No file size limits** — large uploads could exhaust disk space
5. **Prompt injection** — malicious input could manipulate LLM behavior
6. **SSRF via repo cloning** — `git clone` could be used to scan internal networks

### 96. How would you add user authentication?

1. Add a `users` table to the database with hashed passwords (bcrypt)
2. Implement `POST /auth/register` and `POST /auth/login` endpoints
3. Issue JWT tokens on successful login
4. Add a FastAPI middleware/dependency that verifies JWT on every request
5. Scope all data (chats, messages, Qdrant collections) by `user_id`
6. For OAuth: integrate with Google/GitHub OAuth2 flow

### 97. How would you scale the embedding/ingestion pipeline?

1. **Background processing** — Use Celery + Redis as a task queue. Ingestion runs in a background worker, not the API process
2. **Progress tracking** — Store job status in Redis; frontend polls for completion
3. **Batch optimization** — Embed in larger batches (128 instead of implicit batch sizes)
4. **GPU acceleration** — Use a GPU instance for the embedding worker
5. **API-based embeddings** — Switch to OpenAI's embedding API for unlimited parallelism (tradeoff: cost + latency)

### 98. What metrics would you monitor in production?

| Metric | Why |
|---|---|
| LLM response latency (p50, p95, p99) | User experience |
| Cache hit rate | Cost optimization |
| Qdrant query latency | Search performance |
| Ingestion throughput (chunks/second) | Pipeline health |
| Error rate (500s, LLM failures) | Reliability |
| Active concurrent users | Capacity planning |
| Token usage per request | Cost tracking |
| Memory usage (Redis, Qdrant) | Infrastructure health |

### 99. If you could add one feature, what would it be?

**Evaluation pipeline with RAGAS**. Right now, I have no automated way to measure whether my RAG retrieval is improving or degrading as I change chunking strategies, embedding models, or search parameters. An evaluation pipeline with a curated test set of 50+ question-answer pairs would let me run `pytest` and get a quality score, enabling data-driven optimization.

### 100. What's the most important thing you learned from building this project that you'd apply to your next project?

**Start with evaluation, not features.** I built the entire RAG pipeline before having any way to measure its quality. This made it hard to know if changes (different chunk sizes, different embedding models) actually improved results. In my next GenAI project, I'll create a test set and evaluation framework first, then iterate on the pipeline with measurable quality feedback. This is the same principle as TDD (Test-Driven Development) applied to AI systems.

---

> 💡 **Tip**: Practice explaining any 10 of these questions out loud in under 2 minutes each. The interviewer is testing your **depth of understanding**, not your ability to recite — so focus on the *why* behind each decision.
