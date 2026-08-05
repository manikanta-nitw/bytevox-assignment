ByteVox Neural Core
Version 3.2.0 — Production Candidate · DOC-ID BVX-NC-SDD-032 · Classification: INTERNAL / ENGINEERING

Enterprise-grade Retrieval-Augmented Generation (RAG) evaluation and ingestion engine: ingests proprietary platform documentation, indexes semantic embeddings, and returns precise, context-bounded answers to complex technical queries.

Setup note: this README follows the stack and parameters specified in the SDD (BVX-NC-SDD-032 v3.2.0). Where the SDD does not pin an exact name (repo layout, endpoint paths, env var names), conventions are proposed and marked as such — reconcile them with your actual repository before use.

Table of contents
Overview
Architecture
Prerequisites
Setup
Configuration
Ingestion
Running the system
Query flow
API reference
Performance envelope
Evaluation & SLOs
Troubleshooting
Production roadmap
Overview
The system is deliberately prototyped on consumer-grade, CPU-only hardware to establish an honest performance floor before committing capital to accelerated infrastructure. The key measured finding (SDD §06):

Vector similarity search is effectively free at this scale (<15 ms), while CPU-bound autoregressive generation dominates end-to-end latency (~41.5 s per query).

Design goals (SDD §02):

Grounded answers only — every response derives exclusively from retrieved documentation context; the model is prompted to refuse when context is insufficient.
Deterministic, inspectable retrieval — source chunks, similarity scores, and prompt composition are surfaced in the evaluation dashboard for auditability.
Local-first reproducibility — the full stack runs on a single workstation with no external API dependencies.
Clean scale-out seams — each tier (API, vector store, inference) is independently replaceable with its managed/accelerated production equivalent.
Architecture
Tier	Technology	Responsibility
Frontend	React · Vite · Tailwind CSS v3	Evaluation dashboard — telemetry panels, animated source disclosure, similarity-score inspection
API gateway	Python · FastAPI	RESTful endpoints, CORS middleware, async request validation, structured telemetry logging
Vector store	Qdrant (local, file-based persistence)	HNSW index, cosine distance, approximate nearest neighbor search (k=3)
Inference	SentenceTransformers · HuggingFace	all-MiniLM-L6-v2 embeddings (384-d); SmolLM-135M local CPU-bound generation
┌───────────────────────────────────────────────────────────┐
│ Evaluation dashboard — React · Vite · Tailwind CSS v3      │
└──────────────────────────┬────────────────────────────────┘
                           │ REST / JSON
┌──────────────────────────▼────────────────────────────────┐
│ API gateway — Python · FastAPI                            │
│ CORS · async validation · structured telemetry            │
└───────────────┬────────────────────────────┬──────────────┘
                │ ANN query (k=3)             │ grounded prompt
┌───────────────▼──────────────┐  ┌───────────▼──────────────┐
│ Vector storage — Qdrant      │  │ Inference pipeline       │
│ HNSW · cosine · file-based   │  │ all-MiniLM-L6-v2 (384-d) │
│ persistence                  │  │ SmolLM-135M · CPU-bound  │
└──────────────────────────────┘  └──────────────────────────┘
See bytevox_reflection.md for a technical review of this architecture.

Prerequisites
Requirement	Version / Notes
Python	3.10+
Node.js	18+ (with npm)
Qdrant	Local binary or Docker image (docs)
RAM	~16 GB recommended (reference profile is consumer CPU-only)
Network	Required on first run to download HuggingFace model weights
Setup
1. Backend
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
backend/requirements.txt (proposed — pin versions for reproducibility):

fastapi
uvicorn[standard]
qdrant-client
sentence-transformers
langchain-text-splitters
pydantic-settings
2. Vector store (Qdrant, local)
The SDD specifies local file-based persistence (no external service). Either option keeps storage on disk under ./qdrant_storage:

Option A — local binary (recommended for the SDD profile; no container runtime needed):

# Download the qdrant binary for your platform, then:
./qdrant                       # serves on http://localhost:6333, persists to ./qdrant_storage
Option B — Docker:

docker run -p 6333:6333 -v "$(pwd)/qdrant_storage:/qdrant/storage" qdrant/qdrant
Verify: curl http://localhost:6333/healthz → {"status":"ok"}

3. Frontend
cd frontend
npm create vite@latest . -- --template react
npm install
npm install -D tailwindcss@^3 postcss autoprefixer   # Tailwind v3 per SDD
npx tailwindcss init -p
Then add the template paths to tailwind.config.js and the Tailwind directives to src/index.css per the Tailwind v3 docs.

4. Configuration
Copy backend/.env.example to backend/.env and adjust:

cp backend/.env.example backend/.env
Variable	Default	Notes
QDRANT_URL	http://localhost:6333	Local Qdrant endpoint
QDRANT_COLLECTION	bytevox_docs	Created on first ingestion
EMBEDDING_MODEL	sentence-transformers/all-MiniLM-L6-v2	384-d dense embeddings (model card)
LLM_MODEL	HuggingFaceTB/SmolLM-135M-Instruct	SDD specifies "SmolLM-135M"; exact checkpoint not pinned — SmolLM-135M-Instruct is the closest match, SmolLM2-135M-Instruct is a valid alternative
CHUNK_SIZE	512	Tokens per chunk (SDD §04 — tuned for technical manuals)
CHUNK_OVERLAP	50	Token overlap between chunks (SDD §04)
TOP_K	3	Number of chunks retrieved per query (SDD §05)
SIMILARITY_THRESHOLD	(set per eval set)	Below this, the model takes the refusal path
CORS_ORIGINS	http://localhost:5173	Vite dev server origin
API_PORT	8000	Uvicorn port
DATA_DIR	../data/docs	Source documentation for ingestion
LOG_LEVEL	INFO	Structured telemetry logging
Ingestion
Pipeline: normalize → split → embed → upsert (SDD §04). Chunking uses RecursiveCharacterTextSplitter with the configured CHUNK_SIZE/CHUNK_OVERLAP, splitting hierarchically across paragraph, sentence, and word boundaries.

# Ingest (or re-ingest) all documents under data/docs (proposed CLI — align with repo)
python -m app.ingestion --input data/docs
Ingestion is idempotent — safe to re-run; re-index on documentation release events is the intended refresh mechanism (SDD §08).
Each chunk is upserted with payload metadata: source document ID, chunk index, and the embedding vector.
Collection is created on first upsert with HNSW index and cosine distance (SDD §03).
Running the system
Terminal 1 — API gateway:

cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
Interactive API docs: http://localhost:8000/docs

Terminal 2 — frontend:

cd frontend
npm run dev
Dashboard: http://localhost:5173

Terminal 3 — Qdrant (if not already running, per step 2).

Query flow
The dashboard sends the question to the API gateway over REST/JSON.
The gateway embeds the query into a 384-d vector (all-MiniLM-L6-v2, <40 ms).
Qdrant performs an ANN search over the HNSW index using cosine distance, retrieving the top k=3 chunks (recall > 0.95, <15 ms at prototype collection size).
If no chunk clears the relevance threshold, the model takes the refusal path and states the documentation does not cover the question.
Otherwise, retrieved chunks — labeled with source document and similarity score — are injected into a strict context-only prompt.
SmolLM-135M generates the answer locally. On the CPU-only reference profile this takes ≈ 41.5 s per query — this is expected and by design (see Performance envelope).
The dashboard discloses every retrieved source alongside the answer for per-query audit.
API reference
Conventional endpoints — the SDD specifies behavior, not paths; align with the repo.

Endpoint	Method	Body	Response
/api/query	POST	{"question": "..."}	{"answer": "...", "sources": [{"document": "...", "score": 0.87, "chunk": "..."}], "refused": false}
/api/ingest	POST	{"path": "data/docs"}	{"chunks_upserted": 1234, "documents": 12}
/api/health	GET	—	{"status": "ok", "qdrant": "ok", "models_loaded": true}
Performance envelope
Measured on the reference hardware profile (consumer CPU, no accelerators) — SDD §06:

Stage	Measured latency	Bottleneck class
Query embedding	< 40 ms	CPU — single forward pass, negligible
Vector similarity search	< 15 ms	Memory-bound HNSW graph traversal; effectively free
Token generation (SmolLM-135M)	≈ 41.5 s / query	CPU matrix multiplication; dominates end-to-end latency
Architectural implication (SDD §06): retrieval scalability and generation scalability diverge fundamentally — the vector tier scales with memory and index sharding, the generation tier only with accelerated compute. Production design must decouple the two; this drives every item in the roadmap.

Evaluation & SLOs
Retrieval recall is measured against the curated evaluation set (eval/ in the proposed layout) — target ≥ 0.95.
Re-run the eval set on every ingestion or embedding-model change to track drift (SDD §08).
Production SLO targets (post-roadmap, SDD §07): p95 end-to-end answer latency ≤ 2.5 s (cache miss) / ≤ 100 ms (cache hit); 99.9% monthly availability; retrieval recall ≥ 0.95.
Troubleshooting
Symptom	Cause / fix
Answers take ~40 s	Expected on the CPU-only prototype — the entire production roadmap exists to fix this (GPU inference). Not a bug.
Model download fails / slow on first query	First run downloads weights from HuggingFace. Pre-cache with HF_HOME set, or pre-download: python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
CORS errors in the dashboard	Check CORS_ORIGINS in .env matches the Vite origin (default http://localhost:5173).
Connection refused on Qdrant	Qdrant binary/container not running on port 6333.
Empty answers / refusals for in-scope questions	SIMILARITY_THRESHOLD too strict, or documentation not yet ingested.
Out of memory during ingestion	Reduce upsert batch size, or raise RAM — do not lower CHUNK_SIZE without re-running the eval set.
Production roadmap
Per SDD §07, ordered by expected latency impact (target: 50,000 DAU):

GPU inference — dedicated vLLM instances on NVIDIA A100/H100, decoupled from the API tier → generation < 1.5 s.
Semantic caching — Redis layer caching query embeddings and pre-computed responses → frequent questions < 5 ms.
Horizontal API scaling — Dockerized FastAPI on Kubernetes (EKS/GKE) behind an Elastic Load Balancer.
Distributed vector tier — managed Qdrant Cloud with multiple read replicas.
SLO targets: p95 ≤ 2.5 s (miss) / ≤ 100 ms (hit) · 99.9% availability · recall ≥ 0.95.

Related documents
bytevox_reflection.md — technical review of the v3.2.0 design (open questions, under-weighted risks, sign-off blockers)
SDD BVX-NC-SDD-032 v3.2.0 — source of all stack, parameter, and performance claims above
License & classification
INTERNAL / ENGINEERING — © 2026 ByteVox. Not for external distribution. Promotion of v3.2.0 to production requires sign-off from Engineering and Infrastructure leads (SDD §09).