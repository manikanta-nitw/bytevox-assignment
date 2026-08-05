# ByteVox Neural Core

> Enterprise-grade Retrieval-Augmented Generation (RAG) evaluation system — ingests proprietary platform documentation, indexes semantic embeddings, and returns precise, context-bounded answers to complex technical queries. Runs **100% locally** on CPU-only hardware with no external API dependencies.

---

## Features

- **Grounded answers only** — strict context-only prompting; the model answers exclusively from retrieved documentation
- **Deterministic guardrails** — greetings and off-topic queries are intercepted before ever reaching the LLM
- **Inspectable retrieval** — every answer returns its source documents for per-query audit
- **Fully local & free** — no API keys, no cloud calls, complete data privacy
- **Clean scale-out seams** — each tier (API, vector store, inference) is independently swappable with its production equivalent

## Architecture

```
┌─────────────────────────────────────────────────────┐
│   Evaluation Dashboard — React · Vite · Tailwind    │
└─────────────────────────┬───────────────────────────┘
                          │  REST / JSON
┌─────────────────────────▼───────────────────────────┐
│   API Gateway — Python · FastAPI  (api.py)          │
│   CORS · request validation · guardrails            │
└──────────────┬──────────────────────┬───────────────┘
               │ ANN query (k=3)      │ grounded prompt
┌──────────────▼─────────────┐  ┌─────▼───────────────────┐
│  Vector Store — Qdrant     │  │  Inference Pipeline     │
│  HNSW · cosine distance    │  │  all-MiniLM-L6-v2 (384d)│
│  local file persistence    │  │  SmolLM-135M-Instruct   │
│  (./qdrant_data)           │  │  CPU-bound generation   │
└────────────────────────────┘  └─────────────────────────┘
```

| Tier | Technology | Responsibility |
|------|-----------|----------------|
| Frontend | [React](https://vitejs.dev/) · Vite · [Tailwind CSS v3](https://tailwindcss.com/) | Evaluation dashboard with source disclosure |
| API Gateway | Python · [FastAPI](https://fastapi.tiangolo.com/) | REST endpoint, CORS, deterministic guardrails |
| Vector Store | [Qdrant](https://qdrant.tech/documentation/) (local persistent) | HNSW indexing, sub-millisecond similarity search |
| Inference | [SentenceTransformers](https://www.sbert.net/) · HuggingFace | [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) embeddings · [SmolLM-135M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM-135M-Instruct) generation |

See [ARCHITECTURE.md](ARCHITECTURE.md) for design rationale, chunking mechanics, and the 50,000-DAU scaling protocol.

## Project Structure

```
bytevox-assignment/
├── data/              # Source documentation corpus (.txt / .pdf / .md)
├── frontend/          # React + Vite + Tailwind evaluation dashboard
├── results/           # Test-run reports and evaluation output
├── api.py             # FastAPI gateway — retrieval + grounded generation
├── ingest.py          # Ingestion: load → chunk (512/50) → embed → upsert
├── evaluate.py        # Automated 5-question benchmark against the API
└── ARCHITECTURE.md    # Design decisions & scaling roadmap
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Internet connection on first run (downloads HuggingFace model weights)

### 1 — Backend setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install fastapi "uvicorn[standard]" langchain-community langchain-huggingface \
    langchain-qdrant langchain-text-splitters transformers sentence-transformers \
    pymupdf python-dotenv requests
```

### 2 — Ingest the documentation

Place your documentation files (`.txt`, `.pdf`, `.md`) inside the `data/` folder, then run:

```bash
python ingest.py
```

This loads all documents, splits them with `RecursiveCharacterTextSplitter` (**512-token chunks, 50-token overlap**), embeds each chunk with all-MiniLM-L6-v2, and upserts the vectors into a local Qdrant collection (`bytevox_docs`) persisted at `./qdrant_data`.

### 3 — Start the API

```bash
uvicorn api:app --reload --port 8000
```

The first run downloads the embedding and generation models — allow a few minutes.

### 4 — Start the dashboard

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and start asking questions.

## API Reference

### `POST /query`

**Request** (both `question` and `query` keys are accepted):

```json
{ "question": "What is the memory limit for the cpu-small compute profile?" }
```

**Response:**

```json
{
  "answer": "The cpu-small compute profile has a memory limit of ...",
  "sources": ["nexus_docs.md"]
}
```

**Try it with curl:**

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the Control Plane do in the Nexus architecture?"}'
```

**Guardrails:** greetings ("hi", "hello", ...) and off-topic queries (weather, sports, movies, ...) are answered deterministically with a refusal message — they never consume LLM compute.

## Evaluation

Run the automated benchmark (API must be running):

```bash
python evaluate.py
```

It fires 4 benchmark questions at the API and reports per-query latency, retrieved sources, generated answers, and a final score. Full test-run reports live in [`results/`](results/).

## Performance Profile (CPU-only)

| Stage | Latency | Bottleneck class |
|-------|---------|------------------|
| Query embedding | < 40 ms | CPU — single forward pass, negligible |
| Vector similarity search | < 15 ms | Memory-bound HNSW traversal — effectively free |
| Token generation (SmolLM-135M) | ≈ 40 s / query | CPU matrix multiplication — dominates end-to-end latency |

> **Key finding:** retrieval is effectively free at this scale, while CPU-bound autoregressive generation dominates latency. The production architecture therefore scales the generation tier independently of retrieval.

## Scaling Roadmap — 50,000 DAU

1. **GPU inference** — decouple generation onto dedicated vLLM instances (NVIDIA A100/H100), cutting latency from ~40 s to under 2 s
2. **Semantic caching** — Redis layer caching query embeddings and pre-computed responses; frequent questions bypass the LLM entirely
3. **Horizontal API scaling** — Dockerized FastAPI orchestrated with Kubernetes (EKS/GKE) behind an Elastic Load Balancer
4. **Distributed vector tier** — migrate local Qdrant to managed Qdrant Cloud with read replicas

Full details in [ARCHITECTURE.md](ARCHITECTURE.md).

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Answers take ~40 s | Expected on CPU-only hardware — see the scaling roadmap above |
| Slow first query | Model weights download on first run; subsequent runs use the local cache |
| `No documents found` during ingestion | Ensure `.txt` / `.pdf` / `.md` files exist inside `data/` |
| CORS errors in dashboard | The API allows all origins by default; verify the API is running on port 8000 |
| Refusals for valid questions | Re-run `python ingest.py` to make sure the corpus is indexed |
