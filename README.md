# 🧠 PlacementBrain

> **Personal AI Knowledge Base for Campus Placement Preparation**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://react.dev)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC382D?logo=data:image/png;base64,&logoColor=white)](https://qdrant.tech)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)

---

## What It Does

PlacementBrain solves the **scattered knowledge problem** every student faces during campus placement season:

- 📚 **Ingest Everything** — Upload PDFs (notes, textbooks), Excel sheets (company data), code files (DSA solutions, projects), and even entire GitHub repos. PlacementBrain chunks, embeds, and indexes everything automatically.
- 🔍 **Hybrid RAG Search** — Combines semantic search (understands meaning) with BM25 keyword search using Reciprocal Rank Fusion — finds relevant content even when you don't remember exact terms.
- 🤖 **Conversational AI Agent** — Ask questions naturally. The ReAct agent decides whether to search your knowledge base, generate quizzes, explain code, or analyze resume-JD fit.
- ⚡ **Semantic Caching** — Repeated or similar questions are served instantly from Redis cache using embedding similarity — no LLM call needed.
- 🎯 **Placement-Specific Tools** — Quiz generation, resume vs JD comparison, code explanation (with complexity analysis), and gap analysis — all powered by your own uploaded materials.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     React + Vite Frontend                     │
│               (SSE Streaming, Dark Theme UI)                  │
└─────────────────────────┬────────────────────────────────────┘
                          │ HTTP / SSE
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                            │
│  ┌─────────┐  ┌──────────┐  ┌─────────────┐  ┌───────────┐  │
│  │ Ingest  │  │   Chat   │  │   Sources   │  │  Health   │  │
│  │ Router  │  │  Router  │  │   Router    │  │  Check    │  │
│  └────┬────┘  └────┬─────┘  └──────┬──────┘  └───────────┘  │
│       │            │               │                          │
│  ┌────▼────────────▼───────────────▼──────────────────────┐  │
│  │              ReAct Agent (LangChain)                    │  │
│  │  Tools: search_kb | compare_resume | explain_code |     │  │
│  │         generate_quiz                                   │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │                                       │
│  ┌────────────────────▼───────────────────────────────────┐  │
│  │              Hybrid Search Engine                       │  │
│  │     Semantic (Qdrant) + BM25 (in-memory)               │  │
│  │     Reciprocal Rank Fusion                              │  │
│  └────────┬───────────────────────────┬───────────────────┘  │
│           │                           │                       │
│           ▼                           ▼                       │
│  ┌─────────────────┐       ┌──────────────────────┐          │
│  │  Semantic Cache  │       │  Session Memory      │          │
│  │  (Redis + cosim) │       │  (Redis + 24h TTL)   │          │
│  └─────────────────┘       └──────────────────────┘          │
└──────────┬──────────────────────────────┬────────────────────┘
           │                              │
           ▼                              ▼
   ┌───────────────┐            ┌──────────────────┐
   │    Qdrant     │            │      Redis       │
   │  Vector DB    │            │   Cache + Memory │
   │  (port 6333)  │            │   (port 6379)    │
   └───────────────┘            └──────────────────┘
```

---

## Tech Stack

| Component | Technology | Why This Choice |
|-----------|-----------|----------------|
| **Vector DB** | Qdrant | Production-grade, stores metadata + vectors together, scales to millions of points |
| **Semantic Cache** | Redis | Sub-millisecond latency, native TTL support, also used for session memory |
| **Embeddings** | sentence-transformers `all-MiniLM-L6-v2` | Free, runs locally inside Docker, 384-dim — fast and accurate |
| **LLM** | Groq (Llama3-70B) | Free tier available, ~500 tokens/sec inference speed |
| **Backend** | FastAPI | Async native, SSE streaming support, auto-generated API docs |
| **Frontend** | React + Vite + TypeScript | Fast HMR dev experience, type safety, modern tooling |
| **Containerization** | Docker Compose | One-command deployment, isolated services, reproducible |

---

## GenAI Concepts Demonstrated

| Concept | Where Implemented | Interview Talking Point |
|---------|-------------------|------------------------|
| **RAG Pipeline** | `services/rag/` | End-to-end: ingest → chunk → embed → store → retrieve → generate |
| **Hybrid Search** | `hybrid_search.py` | BM25 catches exact keyword matches that semantic search misses |
| **Reciprocal Rank Fusion** | `hybrid_search.py` | RRF with k=60 merges rankings without score normalization |
| **Semantic Caching** | `cache/semantic_cache.py` | Cosine similarity on query embeddings, 0.92 threshold, Redis-backed |
| **ReAct Agent** | `agent/agent.py` | Reason-Act loop: agent decides which tool to call based on query |
| **Tool Use / Function Calling** | `agent/tools.py` | 4 specialized tools the agent can invoke autonomously |
| **Conversation Memory** | `agent/agent.py` | Sliding window (k=10) memory persisted to Redis per session |
| **Source Attribution** | `routers/chat.py` | Every response includes source documents with relevance scores |
| **AST-based Code Chunking** | `ingestion/code_loader.py` | Python AST extracts functions/classes as semantic units vs. blind splitting |
| **SSE Streaming** | `routers/chat.py` | Server-Sent Events for real-time token-by-token response streaming |

---

## Supported Input Types

| Type | Extensions | Chunking Strategy |
|------|-----------|-------------------|
| **PDF** | `.pdf` | Page-by-page extraction, RecursiveCharacterTextSplitter (1000/200) |
| **Excel** | `.xlsx`, `.xls` | Sheet-aware, 20-row groups with cell joining |
| **Code** | `.py`, `.js`, `.ts`, `.java` | Python: AST-based (functions/classes). Others: 50-line sliding window |
| **Markdown** | `.md` | Heading-based splitting with sub-chunking for long sections |
| **Text** | `.txt`, `.json` | RecursiveCharacterTextSplitter (800/150) |
| **Repository** | Git URL | Clones repo, filters files, routes to appropriate loader |

---

## Setup

```bash
# 1. Clone and configure
git clone https://github.com/yourusername/placementbrain.git
cd placementbrain
cp .env.example .env  # Add your GROQ_API_KEY

# 2. Start backend (Docker)
docker compose up -d

# 3. Start frontend
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173** — backend API at **http://localhost:8000/docs**

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ingest/file` | Upload and ingest a file (auto-detects type) |
| `POST` | `/ingest/repo` | Clone and ingest a Git repository |
| `POST` | `/ingest/text` | Ingest raw text directly |
| `GET` | `/chat/stream` | SSE stream — chat with the AI agent |
| `GET` | `/sources` | List all ingested sources with chunk counts |
| `DELETE` | `/sources/{id}` | Delete a source and all its chunks |

### Example: Upload a file

```bash
curl -X POST http://localhost:8000/ingest/file \
  -F "file=@notes.pdf" \
  -F "source_type=pdf"
```

### Example: Chat (SSE)

```bash
curl -N "http://localhost:8000/chat/stream?message=What+is+binary+search&session_id=test123"
```

---

## System Design — "How Would You Scale This?"

| Component | Current (Personal) | Production Scale |
|-----------|-------------------|-----------------|
| **Vector DB** | Single Qdrant container | Qdrant Cloud cluster with sharding + replicas |
| **Embeddings** | In-process SentenceTransformer | Dedicated GPU inference service (Triton/TGI) |
| **LLM** | Groq free tier | Self-hosted vLLM or Groq paid tier with rate limiting |
| **Cache** | Single Redis instance | Redis Cluster with persistence (AOF) |
| **BM25 Index** | In-memory rebuild | Elasticsearch/OpenSearch for distributed full-text search |
| **File Storage** | Docker volume | S3/GCS with signed URLs |
| **API** | Single FastAPI instance | Kubernetes with HPA, behind API Gateway |
| **Frontend** | Vite dev server | Vercel/CloudFront CDN with SSR |

---

## Project Structure

```
placementbrain/
├── docker-compose.yml          # Service orchestration
├── .env.example                # Environment template
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # FastAPI app + startup
│   ├── core/
│   │   ├── config.py           # Pydantic settings
│   │   └── dependencies.py     # Singleton DI container
│   ├── routers/
│   │   ├── ingest.py           # File/repo/text ingestion
│   │   ├── chat.py             # SSE streaming chat
│   │   └── sources.py          # Knowledge base CRUD
│   ├── services/
│   │   ├── ingestion/          # 6 loaders + dispatcher
│   │   ├── rag/                # Embedder, VectorStore, BM25, Hybrid Search
│   │   ├── agent/              # ReAct agent + 4 tools
│   │   └── cache/              # Semantic cache
│   └── models/
│       └── schemas.py          # Pydantic models
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Main layout
│   │   ├── components/         # Chat, Upload, Dashboard
│   │   ├── hooks/              # useSSE, useSources
│   │   ├── api/                # chat, ingest, sources
│   │   └── types/              # TypeScript interfaces
│   └── package.json
└── data/                       # Persistent volumes
    ├── qdrant/
    ├── redis/
    └── uploads/
```

---

## Built By

A student at **IIIT Gwalior** — built for placement preparation, demonstrating production-grade GenAI engineering.

---

## License

MIT
