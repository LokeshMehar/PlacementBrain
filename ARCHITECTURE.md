# PlacementBrain — Architecture, Design Decisions & GenAI Flow

> A complete reference for understanding every engineering decision, tradeoff, and GenAI pipeline in this project — designed to help you confidently answer deep technical questions in interviews.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [High-Level Architecture Diagram](#2-high-level-architecture-diagram)
3. [Component Interaction Flow](#3-component-interaction-flow)
4. [Complete GenAI Pipeline](#4-complete-genai-pipeline)
5. [Retrieval-Augmented Generation (RAG) Deep Dive](#5-retrieval-augmented-generation-rag-deep-dive)
6. [Technology Stack — Choices, Alternatives & Tradeoffs](#6-technology-stack--choices-alternatives--tradeoffs)
7. [Data Flow Diagrams](#7-data-flow-diagrams)
8. [Caching Architecture](#8-caching-architecture)
9. [Database Design](#9-database-design)
10. [Containerization & DevOps](#10-containerization--devops)
11. [Security Considerations](#11-security-considerations)
12. [Scalability Analysis](#12-scalability-analysis)
13. [Known Limitations & Future Improvements](#13-known-limitations--future-improvements)

---

## 1. Project Overview

**PlacementBrain** is a personal AI-powered knowledge base for campus placement preparation. It ingests resumes (PDF), code files (C++, Python, JS, HTML/CSS), markdown notes, and Git repositories into a vector database, then provides an intelligent conversational interface with:

- **Hybrid RAG Search** (Semantic + BM25 keyword search fused via RRF)
- **Resume vs JD Comparison** (automated gap analysis)
- **Code Explanation** (interview-style code walkthroughs)
- **Quiz Generation** (MCQ questions from ingested materials)
- **Mock Interviewer** (5-question adaptive interview sessions with feedback)
- **Multi-chat Threads** with persistent history
- **Semantic Caching** for repeated/similar queries

---

## 2. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER'S BROWSER                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              React + TypeScript Frontend (Vite)               │  │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌───────────────┐  │  │
│  │  │Chat      │ │Source    │ │Quick      │ │Mock Interview │  │  │
│  │  │Window    │ │Manager   │ │Actions    │ │Mode           │  │  │
│  │  └────┬─────┘ └────┬─────┘ └─────┬─────┘ └──────┬────────┘  │  │
│  │       │             │             │              │           │  │
│  │       ▼             ▼             ▼              ▼           │  │
│  │  ┌──────────────────────────────────────────────────────┐    │  │
│  │  │       API Layer (fetch + EventSource SSE)            │    │  │
│  │  └──────────────────────┬───────────────────────────────┘    │  │
│  └─────────────────────────┼────────────────────────────────────┘  │
│                            │ HTTP / SSE                             │
└────────────────────────────┼────────────────────────────────────────┘
                             │  Vite Dev Proxy (/api → :8000)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DOCKER COMPOSE NETWORK (pb-net)                   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │             FastAPI Backend (pb_api :8000)                    │   │
│  │                                                              │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │   │
│  │  │ Routers     │  │ Agent Layer  │  │ Ingestion Pipeline │  │   │
│  │  │ • /chat     │  │ • LangChain  │  │ • PDF Loader       │  │   │
│  │  │ • /ingest   │  │ • ReAct Agent│  │ • Code Loader      │  │   │
│  │  │ • /sources  │  │ • Tool Calls │  │ • Markdown Loader  │  │   │
│  │  │ • /interview│  │ • Streaming  │  │ • Repo Cloner      │  │   │
│  │  └──────┬──────┘  └──────┬───────┘  └────────┬───────────┘  │   │
│  │         │                │                    │              │   │
│  │         ▼                ▼                    ▼              │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │              Service Layer                            │   │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐  │   │   │
│  │  │  │Embedder  │ │Hybrid    │ │Semantic│ │SQLite DB │  │   │   │
│  │  │  │(MiniLM)  │ │Search    │ │Cache   │ │(Chat +   │  │   │   │
│  │  │  │          │ │(RRF)     │ │(Redis) │ │Messages) │  │   │   │
│  │  │  └────┬─────┘ └────┬─────┘ └───┬────┘ └──────────┘  │   │   │
│  │  │       │             │           │                    │   │   │
│  │  └───────┼─────────────┼───────────┼────────────────────┘   │   │
│  └──────────┼─────────────┼───────────┼────────────────────────┘   │
│             │             │           │                             │
│             ▼             ▼           ▼                             │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐               │
│  │  Qdrant      │  │  Qdrant     │  │  Redis 7     │               │
│  │  Vector DB   │  │  (BM25 src) │  │  (Cache)     │               │
│  │  (pb_qdrant) │  │             │  │  (pb_redis)  │               │
│  │  :6333       │  │             │  │  :6379       │               │
│  └──────────────┘  └─────────────┘  └──────────────┘               │
│                                                                     │
│             ┌──────────────────────────────┐                        │
│             │  Groq Cloud API (LLaMA 3.3)  │                        │
│             │  api.groq.com                │                        │
│             └──────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Interaction Flow

```
                    ┌─────────────┐
                    │   User      │
                    │   Browser   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────────┐
              │            │                │
         [Upload File] [Ask Question]  [Start Interview]
              │            │                │
              ▼            ▼                ▼
        ┌──────────┐ ┌──────────┐    ┌──────────────┐
        │ /ingest  │ │/chat/    │    │ /interview/  │
        │ /file    │ │ stream   │    │ start|answer │
        │ /repo    │ │ (SSE)    │    │              │
        └────┬─────┘ └────┬─────┘    └──────┬───────┘
             │             │                 │
             ▼             ▼                 ▼
      ┌────────────┐ ┌──────────┐    ┌────────────┐
      │ Dispatcher │ │ Semantic │    │ Hybrid     │
      │ → Loader   │ │ Cache    │    │ Search     │
      │ → Embedder │ │ Check    │    │ → LLM      │
      │ → Qdrant   │ │ → Agent  │    │ → SQLite   │
      └────────────┘ │ → Stream │    └────────────┘
                     └──────────┘
```

---

## 4. Complete GenAI Pipeline

### 4.1. Ingestion Pipeline (Data → Vectors)

```
User uploads file/repo
        │
        ▼
┌──────────────────────────┐
│   File Type Detection    │
│   (.pdf .py .cpp .md)    │
└──────────┬───────────────┘
           │
     ┌─────┼─────┬──────────┬──────────┐
     ▼     ▼     ▼          ▼          ▼
   PDF   Code  Markdown   Text   Git Repo
  Loader Loader Loader   Loader  Cloner
     │     │     │          │      │
     │  ┌──┘     │          │      │
     │  │ AST-based (Python)│      │
     │  │ Line-based (others)      │
     │  └────────┘          │      │
     ▼                      ▼      ▼
┌──────────────────────────────────────┐
│        Chunking Layer                │
│  • PDF: RecursiveCharacterSplitter   │
│    (1000 chars, 200 overlap)         │
│  • Code: AST nodes OR 50-line        │
│    windows with 10-line overlap      │
│  • Markdown: Header-based sections   │
│  • Text: 500-char recursive split    │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│   SentenceTransformer Embedding      │
│   Model: all-MiniLM-L6-v2           │
│   Dimension: 384                     │
│   Normalization: L2-normalized       │
│   Batch processing via .encode()     │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│   Qdrant Vector DB Upsert           │
│   • Collection: "placementbrain"     │
│   • Distance: COSINE                 │
│   • Batch size: 100 points           │
│   • Payload: text + metadata         │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│   BM25 Index Rebuild                 │
│   • Scrolls all Qdrant documents     │
│   • Tokenizes via .lower().split()   │
│   • Rebuilds BM25Okapi in-memory     │
└──────────────────────────────────────┘
```

### 4.2. Query Pipeline (Question → Streamed Answer)

```
User sends message
        │
        ▼
┌──────────────────────┐
│  Save to SQLite DB   │
│  (human message)     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────┐
│        SEMANTIC CACHE CHECK          │
│                                      │
│  Step 1: Exact String Match (O(1))   │
│    SHA-256 hash → Redis GET          │
│    Hit? → Stream cached response     │
│                                      │
│  Step 2: Semantic Similarity         │
│    Embed query → Compare with cached │
│    embeddings (cosine similarity)    │
│    Threshold: 0.97                   │
│    Hit? → Stream cached response     │
│                                      │
│  Miss? → Continue to Agent           │
└──────────────┬───────────────────────┘
               │ Cache Miss
               ▼
┌──────────────────────────────────────┐
│   LANGCHAIN ReAct AGENT              │
│                                      │
│  1. Load session memory from SQLite  │
│     (last 10 messages via            │
│      ConversationBufferWindowMemory) │
│                                      │
│  2. System Prompt instructs agent:   │
│     • Use tools ONLY when needed     │
│     • Answer general Q's directly    │
│                                      │
│  3. Agent decides: tool call or      │
│     direct response (max 5 iters)    │
│                                      │
│  Available Tools:                    │
│  ┌────────────────────────────┐      │
│  │ search_knowledge_base     │      │
│  │ compare_resume_jd         │      │
│  │ explain_code              │      │
│  │ generate_quiz             │      │
│  └────────────────────────────┘      │
│                                      │
│  4. If tool called → Hybrid Search:  │
│     ┌────────────────────────┐       │
│     │ Semantic Search (top20)│       │
│     │ BM25 Search    (top20)│       │
│     │         │              │       │
│     │    RRF Fusion (k=60)   │       │
│     │         │              │       │
│     │    Return top_k        │       │
│     └────────────────────────┘       │
│                                      │
│  5. LLM generates final answer       │
│     using retrieved context          │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│    ASYNC STREAMING (SSE)             │
│                                      │
│  • AsyncIteratorCallbackHandler      │
│  • Tokens yielded via asyncio queue  │
│  • Each token → JSON SSE event      │
│    {"type":"token","data":"..."}      │
│  • Final event: {"type":"done",      │
│    "sources": [...]}                 │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│   POST-STREAM ACTIONS                │
│                                      │
│  • Cache response in Redis           │
│    (exact + semantic keys)           │
│  • Save AI message to SQLite         │
│  • Attach source metadata            │
└──────────────────────────────────────┘
```

---

## 5. Retrieval-Augmented Generation (RAG) Deep Dive

### 5.1. Why Hybrid Search (not pure semantic)?

| Approach | Strengths | Weaknesses |
|---|---|---|
| **Pure Semantic** | Great for conceptual similarity, paraphrased queries | Misses exact keyword matches (e.g., function names `mergeSort`) |
| **Pure BM25** | Great for exact term matching, fast | Cannot understand meaning; "linked list traversal" ≠ "iterate through nodes" |
| **Hybrid (our choice)** | Best of both worlds; keyword precision + semantic understanding | Slightly more complex; needs index maintenance |

### 5.2. Reciprocal Rank Fusion (RRF)

We use RRF to merge the two ranked lists. The formula for each document `d`:

```
RRF_score(d) = Σ  1 / (k + rank_i(d))
```

Where:
- `k = 60` (smoothing constant — standard in literature)
- `rank_i(d)` = position of document `d` in ranked list `i`

**Why RRF over other fusion methods?**

| Method | Pros | Cons | Our Choice |
|---|---|---|---|
| **RRF** | Score-agnostic, simple, robust | Ignores magnitude of original scores | ✅ Chosen |
| **Linear Combination** | Uses actual scores | Requires score normalization; BM25 & cosine scores are on different scales | ❌ |
| **CombMNZ** | Rewards docs found by multiple methods | More complex, marginal gains | ❌ |
| **Learned Fusion** | Optimal weights | Needs training data we don't have | ❌ |

### 5.3. Embedding Model

| Model | Dimensions | Speed | Quality | Our Choice |
|---|---|---|---|---|
| **all-MiniLM-L6-v2** | 384 | ⚡ Fast (CPU-friendly) | Good for general text | ✅ Chosen |
| all-mpnet-base-v2 | 768 | Slower | Slightly better quality | ❌ Too slow for CPU |
| text-embedding-3-small (OpenAI) | 1536 | API call | Very good | ❌ Adds API dependency + cost |
| nomic-embed-text | 768 | Moderate | Good for code | ❌ Larger memory footprint |
| CodeBERT | 768 | Slow | Best for pure code search | ❌ Not general-purpose enough |

**Why all-MiniLM-L6-v2?**
- Runs entirely on CPU inside Docker — zero API costs
- 384 dimensions means smaller Qdrant storage footprint
- ~80ms per batch of 32 texts on CPU — acceptable for our scale
- L2-normalized output works perfectly with cosine distance

---

## 6. Technology Stack — Choices, Alternatives & Tradeoffs

### 6.1. LLM Provider: Groq (LLaMA 3.3 70B)

| Provider | Model | Latency | Cost | Our Choice |
|---|---|---|---|---|
| **Groq** | LLaMA 3.3 70B Versatile | ~200ms TTFT | Free tier available | ✅ Chosen |
| OpenAI | GPT-4o | ~500ms | $2.50/M input tokens | ❌ Cost at scale |
| Anthropic | Claude 3.5 Sonnet | ~400ms | $3/M input tokens | ❌ Cost |
| Ollama (local) | LLaMA 3 8B | ~2s TTFT | Free | ❌ Needs GPU; quality too low for 70B |
| Google | Gemini 1.5 Flash | ~300ms | Free tier limited | ❌ Rate limits; less tool-calling support |

**Why Groq?**
- **Speed**: Groq's LPU (Language Processing Unit) hardware delivers the fastest inference — critical for streaming UX
- **Free tier**: Generous enough for personal/demo use
- **Tool calling**: Native support for LangChain function calling
- **Tradeoff**: Rate limits on free tier (429 errors under heavy load); no data privacy guarantees

### 6.2. Vector Database: Qdrant

| Database | Hosting | Filtering | Performance | Our Choice |
|---|---|---|---|---|
| **Qdrant** | Self-hosted (Docker) | Rich payload filters | Very fast ANN | ✅ Chosen |
| Pinecone | Cloud-managed | Good filtering | Fast | ❌ Requires cloud account; vendor lock-in |
| Weaviate | Self-hosted | GraphQL-based | Good | ❌ Heavier resource usage |
| ChromaDB | In-process | Basic | Fast for small datasets | ❌ Not production-grade; no Docker clustering |
| FAISS | In-process | None (manual) | Fastest raw ANN | ❌ No metadata filtering; no persistence by default |
| pgvector | Postgres extension | SQL filtering | Moderate | ❌ Slower ANN; needs Postgres setup |

**Why Qdrant?**
- Official Docker image — single `docker pull` and running
- Payload-based filtering (e.g., `source_type = "code"`) without separate metadata store
- HNSW index with configurable parameters
- REST + gRPC APIs
- **Tradeoff**: More memory-intensive than FAISS for very large datasets; self-managed (no auto-backups)

### 6.3. Cache Layer: Redis

| Solution | Type | Speed | Persistence | Our Choice |
|---|---|---|---|---|
| **Redis 7** | In-memory KV store | Sub-ms reads | AOF/RDB snapshots | ✅ Chosen |
| Memcached | In-memory KV | Sub-ms | No persistence | ❌ No TTL flexibility; no scan |
| In-process dict | Python dict | Instant | Lost on restart | ❌ Not shared across workers |
| DynamoDB | Cloud KV | ~5ms | Fully managed | ❌ AWS dependency; overkill |

**Why Redis?**
- TTL-based auto-expiry (1 hour default) — prevents stale cache
- `SCAN` iterator for namespace-scoped invalidation (`semcache:chat_id:*`)
- Docker image is 30MB (Alpine) — minimal overhead
- **Tradeoff**: Volatile — cache is lost on restart (acceptable for a cache layer)

### 6.4. Backend Framework: FastAPI

| Framework | Async | Performance | Ecosystem | Our Choice |
|---|---|---|---|---|
| **FastAPI** | Native async/await | Very fast (Starlette) | Pydantic, OpenAPI | ✅ Chosen |
| Flask | Via extensions | Moderate | Mature but sync-first | ❌ No native async; no auto-docs |
| Django | Channels (complex) | Moderate | Batteries-included | ❌ Overkill; ORM not needed |
| Express.js | Event loop | Fast | Huge npm ecosystem | ❌ Python ML ecosystem needed |

**Why FastAPI?**
- Native `async/await` — critical for SSE streaming and concurrent LLM calls
- Automatic OpenAPI docs at `/docs`
- Pydantic models for request/response validation
- First-class Server-Sent Events support via `sse-starlette`
- **Tradeoff**: Python GIL limits true parallelism (mitigated by async I/O)

### 6.5. Frontend: React + TypeScript + Vite

| Choice | Build Speed | DX | Type Safety | Our Choice |
|---|---|---|---|---|
| **Vite + React + TS** | ~200ms HMR | Excellent | Full TypeScript | ✅ Chosen |
| Create React App | Slow (Webpack) | Good | TS optional | ❌ Deprecated; slow builds |
| Next.js | Moderate | Great | Full TS | ❌ SSR overkill for SPA |
| Vue + Vite | Fast | Great | TS support | ❌ Smaller ecosystem for our needs |
| Svelte | Very fast | Good | TS optional | ❌ Less mature for complex UIs |

### 6.6. Real-time Communication: Server-Sent Events (SSE)

| Method | Direction | Complexity | Browser Support | Our Choice |
|---|---|---|---|---|
| **SSE (EventSource)** | Server → Client | Low | All modern browsers | ✅ Chosen |
| WebSocket | Bidirectional | Higher | All modern browsers | ❌ Overkill — we only stream one direction |
| Long Polling | Simulated push | Medium | Universal | ❌ Wasteful; higher latency |
| HTTP Streaming | Server → Client | Low | Varies | ❌ Less structured than SSE |

**Why SSE?**
- LLM token streaming is inherently one-directional (server → client)
- Native `EventSource` browser API — no library needed
- Auto-reconnection built in
- Works through HTTP/1.1 proxies
- **Tradeoff**: Max 6 concurrent connections per domain in HTTP/1.1 (not an issue for single-user app)

### 6.7. Agent Framework: LangChain (ReAct Pattern)

| Framework | Tool Calling | Streaming | Community | Our Choice |
|---|---|---|---|---|
| **LangChain** | StructuredTool | AsyncIteratorCallback | Massive | ✅ Chosen |
| LlamaIndex | Basic | Limited streaming | Growing | ❌ More RAG-focused, less agentic |
| AutoGen | Multi-agent | Complex setup | Growing | ❌ Overkill for single-agent |
| Custom (raw API) | Manual parsing | Full control | N/A | ❌ High dev effort; fragile tool parsing |
| CrewAI | Multi-agent | Good | New | ❌ Too heavy for our use case |

### 6.8. Chat Persistence: SQLite

| Database | Setup | Concurrency | Docker-Friendly | Our Choice |
|---|---|---|---|---|
| **SQLite** | Zero config | Single-writer | File-based | ✅ Chosen |
| PostgreSQL | Server setup | Multi-writer | Docker image | ❌ Overkill for personal app |
| MongoDB | Server setup | Multi-writer | Docker image | ❌ Additional container; not needed |
| Aiven Cloud PG | Managed | Full | Connection string | 🔮 Future option |

**Why SQLite?**
- Zero configuration — just a file
- Perfect for single-user personal app
- ACID-compliant
- No additional Docker container needed
- **Tradeoff**: Single-writer limitation; not suitable for multi-user production deployment; file locking issues on bind-mounted Docker volumes (solved by using container-internal path)

### 6.9. Containerization: Docker Compose

| Solution | Complexity | Portability | Orchestration | Our Choice |
|---|---|---|---|---|
| **Docker Compose** | Low | High | Basic multi-service | ✅ Chosen |
| Kubernetes | High | Very high | Full orchestration | ❌ Overkill for personal project |
| Podman Compose | Low | High | Similar to Compose | ❌ Less community support |
| Bare metal | None | Low | Manual | ❌ "Works on my machine" problems |

---

## 7. Data Flow Diagrams

### 7.1. File Upload Flow

```
Browser                  FastAPI              Disk        Embedder         Qdrant
   │                        │                  │             │               │
   │──POST /ingest/file────▶│                  │             │               │
   │  (multipart form)      │                  │             │               │
   │                        │──save to disk────▶│             │               │
   │                        │                  │             │               │
   │                        │──dispatch()──────│─────────────│               │
   │                        │  (pdf_loader /   │             │               │
   │                        │   code_loader)   │             │               │
   │                        │                  │             │               │
   │                        │──embed_batch()───│────────────▶│               │
   │                        │                  │     384-dim │               │
   │                        │                  │    vectors  │               │
   │                        │──upsert_chunks()─│─────────────│──────────────▶│
   │                        │                  │             │  PointStruct  │
   │                        │──rebuild BM25────│─────────────│◀──scroll all──│
   │                        │                  │             │               │
   │◀─IngestResponse────────│                  │             │               │
   │  {chunk_count, status}  │                 │             │               │
```

### 7.2. Chat Query Flow (SSE)

```
Browser               FastAPI          Cache       Agent        Qdrant    Groq API
   │                     │               │           │            │          │
   │──GET /chat/stream──▶│               │           │            │          │
   │  ?message=X         │               │           │            │          │
   │  &session_id=Y      │               │           │            │          │
   │                     │──save human───│           │            │          │
   │                     │  msg (SQLite) │           │            │          │
   │                     │               │           │            │          │
   │                     │──cache.get()─▶│           │            │          │
   │                     │               │           │            │          │
   │                     │  [CACHE MISS] │           │            │          │
   │                     │               │           │            │          │
   │                     │──agent.astream()────────▶│            │          │
   │                     │               │           │            │          │
   │                     │               │     [Agent decides: tool call]    │
   │                     │               │           │            │          │
   │                     │               │           │──semantic──▶│          │
   │                     │               │           │  search     │          │
   │                     │               │           │◀─results────│          │
   │                     │               │           │            │          │
   │                     │               │           │──BM25──────▶│          │
   │                     │               │           │  search     │          │
   │                     │               │           │◀─results────│          │
   │                     │               │           │            │          │
   │                     │               │           │──RRF Fusion│          │
   │                     │               │           │            │          │
   │                     │               │           │──prompt + context────▶│
   │                     │               │           │            │    (LLM) │
   │◀─SSE token─────────│◀──token───────│───────────│◀───stream──│──tokens──│
   │◀─SSE token─────────│◀──token───────│           │            │          │
   │◀─SSE token─────────│◀──token───────│           │            │          │
   │                     │               │           │            │          │
   │                     │──cache.set()─▶│           │            │          │
   │                     │──save AI msg──│ (SQLite)  │            │          │
   │◀─SSE done───────────│              │           │            │          │
```

### 7.3. Mock Interview Flow

```
Browser              FastAPI             Qdrant           Groq LLM        SQLite
   │                    │                  │                  │              │
   │──POST /interview/ ─▶│                 │                  │              │
   │   start            │──hybrid_search──▶│                  │              │
   │   {topic}          │◀─context─────────│                  │              │
   │                    │                  │                  │              │
   │                    │──"Generate Q1"───│─────────────────▶│              │
   │                    │◀─question────────│──────────────────│              │
   │                    │                  │                  │              │
   │                    │──create_interview│──────────────────│─────────────▶│
   │                    │──add_message─────│──────────────────│─────────────▶│
   │◀─{Q1, index:1}────│                  │                  │              │
   │                    │                  │                  │              │
   │──POST /interview/ ─▶│                 │                  │              │
   │   answer           │──hybrid_search──▶│                  │              │
   │   {answer}         │◀─context─────────│                  │              │
   │                    │                  │                  │              │
   │                    │──"Evaluate +     │                  │              │
   │                    │   Next Q"────────│─────────────────▶│              │
   │                    │◀─feedback+Q2─────│──────────────────│              │
   │                    │                  │                  │              │
   │                    │──update_interview│──────────────────│─────────────▶│
   │◀─{Q2, feedback}───│                  │                  │              │
   │                    │                  │                  │              │
   │        ... (repeat for Q3, Q4, Q5) ...                                 │
   │                    │                  │                  │              │
   │◀─{status:completed,│                 │                  │              │
   │   final_assessment} │                 │                  │              │
```

---

## 8. Caching Architecture

### Dual-Layer Semantic Cache

```
┌─────────────────────────────────────────────────────┐
│                   QUERY ARRIVES                      │
│                  "What is OOP?"                      │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Layer 1:      │
              │  Exact Match   │────── HIT ──▶ Return cached response
              │  SHA-256 hash  │               (zero LLM cost)
              │  O(1) lookup   │
              └───────┬────────┘
                      │ MISS
                      ▼
              ┌────────────────┐
              │  Layer 2:      │
              │  Semantic      │────── HIT ──▶ Return cached response
              │  Similarity    │               (embedding cost only)
              │  threshold:0.97│
              │  cosine compare│
              └───────┬────────┘
                      │ MISS
                      ▼
              ┌────────────────┐
              │  Full Pipeline │
              │  Agent + RAG   │
              │  + LLM Call    │
              └────────────────┘
```

**Scoping**: Cache keys are **namespaced by `chat_id`**, so Chat A's cached answers don't leak into Chat B.

**TTL**: 1 hour (3600 seconds) — prevents stale answers when new data is ingested.

**Cache Invalidation**: Automatically cleared (`cache.clear()`) after any ingestion operation, since the knowledge base has changed.

---

## 9. Database Design

### 9.1. SQLite Schema (ER Diagram)

```
┌───────────────────┐       ┌───────────────────────┐
│      chats        │       │      messages          │
├───────────────────┤       ├───────────────────────┤
│ id (PK, TEXT)     │──┐    │ id (PK, TEXT)         │
│ title (TEXT)      │  │    │ chat_id (FK → chats)  │
│ created_at (TEXT) │  │    │ role (TEXT)            │
└───────────────────┘  │    │ content (TEXT)         │
                       │    │ created_at (TEXT)      │
                       │    └───────────────────────┘
                       │
                       │    ┌───────────────────────┐
                       │    │     interviews         │
                       │    ├───────────────────────┤
                       └───▶│ id (PK, TEXT)         │
                            │ chat_id (FK → chats)  │
                            │ topic (TEXT)           │
                            │ current_question (TEXT)│
                            │ question_index (INT)   │
                            │ status (TEXT)          │
                            │ created_at (TEXT)      │
                            └───────────────────────┘
```

### 9.2. Qdrant Payload Schema

```json
{
  "text": "The actual chunk content...",
  "source_id": "uuid-of-source",
  "filename": "resume.pdf",
  "source_type": "pdf | code | markdown | text | repo",
  "language": "python | cpp | javascript | ...",      // code only
  "function_name": "merge_sort",                       // Python AST only
  "node_type": "function | class",                     // Python AST only
  "page_number": 3,                                    // PDF only
  "line_range": "1-50",                                // line-based code only
  "repo_url": "https://github.com/user/repo",         // repo only
  "created_at": "2026-06-11T04:13:42+00:00"
}
```

---

## 10. Containerization & DevOps

### Docker Compose Topology

```
┌──────────────────────────────────────────────────────┐
│                docker-compose.yml                     │
│                Network: pb-net (bridge)               │
│                                                      │
│  ┌──────────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   pb_api          │  │ pb_qdrant   │  │pb_redis │ │
│  │   python:3.11-slim│  │ qdrant:latest│ │redis:7  │ │
│  │   :8000           │  │ :6333       │  │:6379    │ │
│  │                   │  │             │  │         │ │
│  │  Volumes:         │  │ Volume:     │  │Volume:  │ │
│  │  ./backend → /app │  │ ./data/     │  │./data/  │ │
│  │  ./data/uploads   │  │  qdrant/    │  │ redis/  │ │
│  │  ./data/hf_cache  │  │             │  │         │ │
│  │                   │  │             │  │         │ │
│  │  Depends on:      │  │             │  │         │ │
│  │  qdrant, redis    │  │             │  │         │ │
│  └──────────────────┘  └─────────────┘  └─────────┘ │
└──────────────────────────────────────────────────────┘
```

**Key Docker decisions:**
- `python:3.11-slim` over `alpine` — better pip compatibility for ML packages (numpy, torch)
- CPU-only PyTorch (`torch==2.4.1+cpu`) — saves ~1.5GB of image size vs CUDA version
- `--reload` flag in CMD — enables hot-reload during development
- HuggingFace cache mounted to host (`./data/hf_cache`) — avoids re-downloading 90MB model on every rebuild

---

## 11. Security Considerations

| Concern | Current State | Production Recommendation |
|---|---|---|
| API Key exposure | `.env` file (gitignored) | Use Docker secrets or Vault |
| CORS | Allows `localhost:3000,5173` | Restrict to production domain |
| Input sanitization | Pydantic validation | Add rate limiting, input length caps |
| SQL Injection | Parameterized queries ✅ | Already protected |
| File upload limits | No enforced size limit | Add max file size (e.g., 50MB) |
| Auth/AuthZ | None (single-user) | Add JWT or OAuth for multi-user |

---

## 12. Scalability Analysis

| Component | Current Scale | Bottleneck At | Horizontal Scaling Strategy |
|---|---|---|---|
| **Qdrant** | ~10K vectors | ~1M vectors | Qdrant Cloud cluster or sharding |
| **Redis** | <100 keys | ~100K keys | Redis Cluster |
| **SQLite** | ~1000 messages | ~100K rows / concurrent writes | Migrate to PostgreSQL (Aiven) |
| **Embedder** | CPU, single-process | >500 docs/batch | GPU instance or API-based embeddings |
| **LLM** | Groq free tier | Rate limits (~30 RPM) | Paid tier or self-hosted Ollama |
| **Backend** | Single uvicorn worker | ~50 concurrent users | Gunicorn with multiple workers |

---

## 13. Known Limitations & Future Improvements

### Current Limitations
1. **Single-user only** — no authentication
2. **CPU-bound embedding** — large repo ingestion is slow
3. **Groq rate limits** — free tier caps requests per minute
4. **No streaming for tool-use intermediate steps** — user sees final response only
5. **BM25 index fully in-memory** — rebuilt from scratch on every ingestion
6. **No chunking strategy for images/diagrams** in PDFs

### Planned Improvements
1. **PostgreSQL migration** (Aiven Cloud) for multi-user chat persistence
2. **Background ingestion** via Celery/Redis task queue with progress bar
3. **Streaming intermediate tool output** to show "Searching knowledge base..." in real-time
4. **Chunk-level relevance feedback** — let users upvote/downvote retrieved chunks
5. **Multi-modal RAG** — support image understanding in PDFs via vision models
6. **Evaluation pipeline** — automated RAG quality scoring (RAGAS framework)
