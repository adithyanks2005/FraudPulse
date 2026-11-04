# 📐 FraudPulse System Architecture & Design

FraudPulse provides automated intelligence, search, and evidence verification over Reserve Bank of India (RBI) publications, financial stability reports, and cyber-risk advisories. This document specifies the service architecture, HTTP API contracts, resilience mechanisms, and PostgreSQL + pgvector database schemas.

---

## 1. System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                       Clients / UI                          │
└──────────────┬───────────────────────────────▲──────────────┘
               │ HTTP Requests                 │ SSE Streams
┌──────────────▼───────────────────────────────┴──────────────┐
│                    FastAPI Application                      │
│                                                             │
│  ┌────────────┐   ┌────────────┐   ┌─────────────────────┐  │
│  │  /health   │   │   /ready   │   │     /usage          │  │
│  │ (Liveness) │   │(Readiness) │   │ (Cost & Token Stats)│  │
│  └────────────┘   └────────────┘   └──────────┬──────────┘  │
│                                               │ Reads       │
│  ┌───────────────────────┐                    ▼             │
│  │        /chat          │          ┌────────────────────┐  │
│  │ (SSE Streaming LLM)   │───────►  │   logs/cost.jsonl  │  │
│  └──────────┬────────────┘  Appends └────────────────────┘  │
│             │                                               │
│  ┌──────────▼────────────┐                                  │
│  │   LLM Provider Layer  │                                  │
│  │  ┌─────────────────┐  │                                  │
│  │  │ Primary Model   │  │                                  │
│  │  └────────┬────────┘  │                                  │
│  │           │ On Error  │                                  │
│  │  ┌────────▼────────┐  │                                  │
│  │  │ Fallback Model  │  │                                  │
│  │  └─────────────────┘  │                                  │
│  └───────────────────────┘                                  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ POST /ask (Week 3 RAG Pipeline)                       │  │
│  └──────────┬────────────────────────────────────────────┘  │
└─────────────┼───────────────────────────────────────────────┘
              │ Vector Similarity Search
┌─────────────▼───────────────────────────────────────────────┐
│              PostgreSQL + pgvector Database                 │
│                                                             │
│  ┌───────────────────┐            ┌──────────────────────┐  │
│  │    documents      │◄───────────│   document_chunks    │  │
│  │ (Metadata/Hashes) │   1 to N   │ (Embeddings & Text)  │  │
│  └───────────────────┘            └──────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. API Endpoints

### 2.1 `GET /health`
* **Purpose**: Fast process liveness probe. Used by Docker, Kubernetes, and uptime monitors.
* **Guarantee**: Never accesses the database or calls external LLM providers. Responds within milliseconds.
* **Response `200 OK`**:
  ```json
  {
    "status": "ok",
    "app": "examate-rag",
    "environment": "production"
  }
  ```

### 2.2 `GET /ready`
* **Purpose**: Application readiness probe. Confirms that background dependencies, configurations, and internal caches are ready to serve traffic.
* **Response `200 OK`**:
  ```json
  {
    "status": "ready",
    "app": "examate-rag",
    "environment": "production"
  }
  ```

### 2.3 `POST /chat`
* **Purpose**: Streaming conversational completions via Server-Sent Events (`text/event-stream`).
* **Request Body**:
  ```json
  {
    "messages": [
      {"role": "system", "content": "You are a banking compliance assistant."},
      {"role": "user", "content": "Summarize RBI trends in card and internet fraud."}
    ],
    "model": "FraudPulse"
  }
  ```
* **Event Stream Formats**:
  * **Text delta**:
    ```text
    data: {"delta": "According "}

    data: {"delta": "to RBI reports... "}
    ```
  * **Error event** (on failure):
    ```text
    event: error
    data: {"error": "LLM provider is currently unavailable"}
    ```
  * **Done event** (final token usage and calculated USD cost):
    ```text
    event: done
    data: {"usage": {"input_tokens": 128, "output_tokens": 64, "estimated": false}, "cost_usd": 0.00015}
    ```

### 2.4 `GET /usage`
* **Purpose**: Reports daily calls, token consumption, and accrued cost in USD, aggregated from `logs/cost.jsonl`.
* **Response `200 OK`**:
  ```json
  {
    "days": {
      "2026-11-04": {
        "calls": 12,
        "input_tokens": 4200,
        "output_tokens": 1850,
        "total_tokens": 6050,
        "cost_usd": 0.00184,
        "errors": 0,
        "fallback_used": 1
      }
    },
    "total_calls": 12,
    "total_cost_usd": 0.00184,
    "total_tokens": 6050
  }
  ```

### 2.5 `POST /ask` (Scheduled for Week 3 RAG)
* **Purpose**: Semantic search and question answering with strict evidence citations.
* **Request Body**:
  ```json
  {
    "question": "What cyber-risk observations did RBI highlight in its latest Financial Stability Report?",
    "top_k": 5
  }
  ```
* **Response Body**:
  ```json
  {
    "answer": "In the latest Financial Stability Report, the RBI noted increasing sophistication in social engineering and third-party vendor cyber risks across regulated entities [1].",
    "citations": [
      {
        "id": 1,
        "document": "RBI_FSR_June_2025.pdf",
        "page": 42,
        "section": "Chapter II: Financial Sector Risks - Cyber Resilience",
        "snippet": "Vulnerabilities associated with third-party service providers and interconnected payment systems have increased..."
      }
    ],
    "model": "FraudPulse-rag-v1",
    "latency_ms": 340.2
  }
  ```

---

## 3. Database Schema (PostgreSQL + pgvector)

The database stores downloaded publication records, extracted text passages, and high-dimensional vector embeddings for similarity search.

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Documents table: tracks ingested reports, release dates, and SHA-256 hashes
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    source_url TEXT NOT NULL,
    publication_type VARCHAR(64) NOT NULL, -- 'FSR', 'AnnualReport', 'PressRelease', etc.
    publication_date DATE NOT NULL,
    sha256 VARCHAR(64) NOT NULL UNIQUE,
    page_count INTEGER NOT NULL CHECK (page_count > 0),
    file_size_bytes BIGINT NOT NULL,
    status VARCHAR(32) DEFAULT 'indexed',  -- 'pending', 'indexed', 'failed'
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_sha256 ON documents(sha256);
CREATE INDEX idx_documents_publication_date ON documents(publication_date);

-- 2. Document Chunks table: stores individual text chunks and their embeddings
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    section_heading VARCHAR(512),
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    embedding vector(1536), -- Standard embedding dimension (e.g. OpenAI / text-embedding-3 or equivalent)
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_document_chunk UNIQUE (document_id, chunk_index)
);

CREATE INDEX idx_document_chunks_doc_page ON document_chunks(document_id, page_number);

-- Vector similarity index using Hierarchical Navigable Small World (HNSW)
CREATE INDEX idx_document_chunks_embedding_hnsw
ON document_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 3. Query & Evaluation Logs table: records evaluation questions and responses
CREATE TABLE query_eval_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    generated_answer TEXT,
    retrieved_chunks JSONB, -- Array of chunk UUIDs and similarity scores
    citations JSONB,        -- Document and page citations provided
    eval_score NUMERIC(3, 2), -- Human or automated correctness score (0.00 - 1.00)
    latency_ms NUMERIC(8, 2),
    cost_usd NUMERIC(8, 6),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_query_eval_created_at ON query_eval_logs(created_at);
```

---

## 4. LLM Resilience & Fallback Strategy

1. **Provider Abstraction**: All LLM backends implement `BaseLLMProvider.stream(request: LLMRequest) -> AsyncIterator[LLMChunk]`.
2. **Failover Execution**:
   - `FallbackLLMProvider` encapsulates a primary model (e.g., fast/cost-effective primary or high-tier model) and a fallback model.
   - If the primary provider raises `LLMUnavailable`, network timeout, or connection refusal before emitting tokens to the client, the provider silently fails over to the secondary provider.
   - The fallback state is tracked in `last_fallback_used`, logged into `cost.jsonl`, and exposed in usage metrics.
3. **Mid-Stream Safety**:
   - If a failure happens *after* chunks have already been emitted to the HTTP client, failover is aborted to prevent corrupting the stream, and an SSE `error` event is emitted.

---

## 5. Cost & Token Accounting Design

1. **Persistence**: Every completion emits an append-only line into `logs/cost.jsonl`.
2. **Data Structure**:
   ```json
   {
     "timestamp": "2026-11-04T17:45:00.123456+00:00",
     "provider": "fake",
     "model": "examate-fake",
     "input_tokens": 48,
     "output_tokens": 16,
     "total_tokens": 64,
     "estimated": true,
     "latency_ms": 42.15,
     "cost_usd": 0.000008,
     "ok": true,
     "fallback_used": false
   }
   ```
3. **Daily Aggregation**: `usage_by_day()` groups entries by UTC calendar date and computes total tokens, calls, errors, fallback frequencies, and cumulative cost.
