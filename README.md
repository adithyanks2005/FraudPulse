# 🛡️ FraudPulse

> **AI-powered RBI financial fraud and cyber-risk intelligence.**  
> Find, compare, and verify what the Reserve Bank of India (RBI) reports about banking fraud, cyber incidents, and digital-payment risks.

**Project status:** In development  
**Primary user:** IT-risk officer at an urban co-operative bank preparing quarterly cyber-risk notes for the board.

---

## 1. The problem

RBI fraud and cyber-risk information is spread across Annual Reports, half-yearly Financial Stability Reports (FSRs), and payment-system publications. These documents arrive on different dates and contain hundreds of pages, making it difficult for an IT-risk officer to find the latest figures and avoid repeating outdated information in board notes.

FraudPulse is being built to collect these publications, make their contents searchable, and return evidence-backed answers with references to the source document and page.

## 2. What FraudPulse will do

- Collect RBI Annual Reports and Financial Stability Reports covering approximately ten years.
- Extract relevant passages about bank fraud, cyber incidents, and digital-payment risks.
- Let users ask questions in natural language.
- Retrieve supporting passages using Retrieval-Augmented Generation (RAG).
- Return answers with document and page citations.
- Detect new or changed RBI publications and re-index only the affected content.
- Show a **“What’s new since your last note?”** view for passages added after a selected date.
- Help users research and prepare quarterly board-risk notes.

> These are project goals. Features are marked as implemented only after they have been built and tested.

## 3. Intended user and example questions

The primary user is an IT-risk officer at an urban co-operative bank in Tiruchirappalli.

Example questions the finished system should help answer:

1. How many digital-payment frauds did banks report in the latest RBI Annual Report?
2. What cyber-risk observations did RBI highlight in its latest Financial Stability Report?
3. How have card and internet-related fraud trends changed over the last five years?
4. Which new RBI fraud or cyber-risk passages have appeared since the date of my previous board note?
5. Which RBI document and page support a particular statistic?

The system must cite its evidence. It should not invent figures when the retrieved documents do not contain an answer.

## 4. Dataset and source

The primary source is the official RBI publications portal:

- [RBI reports and publications](https://rbi.org.in/Scripts/FsReports.aspx)

| Collection | Planned coverage |
|---|---|
| RBI Annual Reports | Approximately 10 years; chapter-wise PDFs where available |
| RBI Financial Stability Reports | Half-yearly reports covering approximately 10 years |
| Minimum corpus target | 30 reports and 6,000+ pages |
| Week 1 collection milestone | 50+ pages |
| Week 2 processing milestone | 500+ pages |

The 6,000+ page figure is the **target corpus**, not a claim that the full dataset has already been collected. Actual downloaded reports and page counts should be recorded in `DATASET.md` and `data/manifest.csv`.

### Dataset handling

- Keep original downloaded PDFs in `data/raw/`; this directory is excluded from Git.
- Keep only small, permitted examples in `data/sample/`.
- Record each download's source URL, download date, byte size, and full SHA-256 hash in `data/manifest.csv`.
- Check the applicable website access rules and reuse terms before collecting or redistributing documents.

## 5. How the system is designed

### RAG question-answering flow

```text
RBI PDFs
   |
   v
PDF text extraction (retain page numbers and headings)
   |
   v
Text cleaning and chunking
   |
   v
Embedding generation
   |
   v
PostgreSQL + pgvector
   |
   |                         User question
   |                               |
   |                               v
   |                        Query embedding
   |                               |
   +----------------------> Similarity search
                                   |
                                   v
                         Relevant source passages
                                   |
                                   v
                              LLM answer
                                   |
                                   v
                     Answer + document/page citations
```

### Incremental indexing flow

```text
Scheduled check of RBI publication pages
                  |
                  v
       Discover PDF links and metadata
                  |
                  v
          Download / hash document
                  |
                  v
       Compare with stored document hash
             /             \
        Unchanged          New/changed
            |                  |
           Skip          Extract affected content
                               |
                         Chunk and embed
                               |
                         Update pgvector
                               |
                         Record update
```

The freshness objective is to make a newly published report searchable within 60 minutes and re-index less than 5% of the existing chunks for a typical single-report update. These are targets to measure, not verified performance claims.

## 6. Technology stack

| Component | Planned technology | Responsibility |
|---|---|---|
| Language | Python 3.12 | Application and data-processing code |
| API | FastAPI | HTTP endpoints |
| LLM | Configured LLM API with fallback model | Answer generation |
| PDF processing | PyMuPDF (planned) | Text extraction with page references |
| Embeddings | Embedding model | Convert chunks and questions to vectors |
| Database | PostgreSQL | Document metadata and application data |
| Vector search | pgvector | Similarity search over embeddings |
| Containers | Docker / Docker Compose | Reproducible local services |
| Tests and CI | pytest, Ruff, GitHub Actions | Quality checks |
| UI | To be selected after backend milestones | User-facing search and updates |

The implementation may be refined as the weekly milestones progress.

## 7. Development schedule and deliverables

The project follows the assigned three-week milestone plan. Each week should end with a working, demonstrable increment and a Git tag.

| Week | Schedule | Work planned | Definition of done |
|---|---|---|---|
| **Week 1 – Foundation and dataset** | Wed 21 – Sat 24 Oct | Create the repository from the Examate template; complete the project README; get FastAPI `/health` running; prepare 10 real research questions; collect the first 50+ RBI PDF pages; document the dataset and add a small sample. | Local health check works; questions and dataset metadata are committed; sample data is present; `week-1` tag is pushed. |
| **Week 2 – LLM and service infrastructure** | Mon 26 – Sat 31 Oct | Integrate LLM calls with a fallback model; expose token and cost usage; run `/health` in Docker and deploy it to a free host; maintain CI checks; document API endpoints and database tables in `DESIGN.md`. | **Completed:** LLM fallback, `/usage` token/cost reporting, Docker health check, live deployment, CI passing on every push, `DESIGN.md`, and `week-2` tag. |


### Work after the three-week milestones

The following capabilities complete the wider project objective and should be scheduled after the core RAG milestone:

1. Expand the corpus toward 30+ reports and 6,000+ pages.
2. Build the daily RBI publication discovery and change-detection job.
3. Implement the “What’s new since your last note?” view.
4. Measure single-report re-indexing time, affected chunk count, and embedding/API cost.
5. Add historical comparisons and support for quarterly board-note research.
6. Improve the user interface, deployment, monitoring, and documentation.

### Progress tracking

The task checklist and daily activity log are maintained in [`PROGRESS.md`](PROGRESS.md). Dataset inventory is maintained in [`DATASET.md`](DATASET.md).

## 8. Repository structure

```text
FraudPulse/
├── .github/
│   └── workflows/
│       └── ci.yml
├── app/
│   ├── Tools/
│   │   ├── downloads.py
│   │   └── url.txt
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   └── schemas.py
├── data/
│   ├── raw/              # Downloaded PDFs; not committed
│   ├── sample/           # Small sample files
│   └── manifest.csv      # Download inventory and hashes
├── docs/
│   └── QUESTIONS.md
├── tests/
│   ├── conftest.py
│   └── test_health.py
├── .env.example
├── .gitignore
├── DATASET.md
├── DESIGN.md
├── Dockerfile
├── PROGRESS.md
├── README.md
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

Additional modules will be added as the LLM, RAG, database, evaluation, and publication-monitoring milestones are implemented.

## 9. Setup and run locally

### Prerequisites

- Python 3.12
- Git
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop (for the database milestone)

### Clone and install

```bash
git clone https://github.com/adithyanks2005/FraudPulse.git
cd FraudPulse

uv python install 3.12
uv venv --python 3.12
uv sync --group dev
```

### Configure environment

Windows:

```powershell
copy .env.example .env
```

Add credentials only when the relevant LLM integration is implemented. Never commit the real `.env` file or API keys.

### Start the API

```bash
uv run uvicorn app.main:app --reload
```

- Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Interactive API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Run the RBI PDF downloader

From the repository root, provide a text file containing **direct PDF URLs**, one per line:

```text
# One direct RBI PDF URL per line
https://www.rbi.org.in/example-report.pdf
```

Run:

```bash
python app/Tools/downloads.py path/to/urls.txt
```

The downloader checks `robots.txt`, uses a delay between requests, retries transient failures, validates PDF responses, saves files under `data/raw/`, and records successful downloads in `data/manifest.csv`. The RBI publications landing page is not itself a PDF URL; use the direct PDF link for each report.

## 10. Evaluation and success metrics

| Metric | Project target |
|---|---:|
| RBI reports in the full corpus | 30+ |
| Pages in the full corpus | 6,000+ |
| Week 1 collected pages | 50+ |
| Week 3 processed pages | 500+ |
| Time for a new report to become searchable | Within 60 minutes |
| Existing chunks re-indexed for a typical single-report update | Less than 5% |
| Answer evidence | Document and page citations |
| Incremental indexing benchmark | Time and estimated cost recorded for one new report |

The RAG evaluation will use the 10 questions in `docs/QUESTIONS.md`. Results, including incorrect or unsupported answers, should be recorded rather than hidden.

## 11. Current implementation status

This repository is under active development. **Week 2 is complete:** LLM calls use a fallback model, `/usage` reports token usage and cost, `/health` runs in Docker and is deployed on a free host, CI passes on every push, and `DESIGN.md` documents the API endpoints and database tables. The parser, pgvector-backed RAG pipeline, citation-based `/ask` endpoint, evaluation, and incremental publication indexing remain Week 3 or later work until implemented and tested.

## 12. Security, accuracy, and disclaimer

- Treat RBI publications as the primary evidence source and retain original URLs and page references.
- Do not present an LLM-generated figure as verified unless it is supported by a retrieved source passage.
- Keep API keys and local environment files out of version control.
- Preserve document hashes so downloaded versions can be identified and compared.
- Verify generated board-note content against the original RBI publication before institutional use.

FraudPulse is an independent academic/technical project. It is not an official RBI product and is not affiliated with or endorsed by the Reserve Bank of India. Outputs are for research support and must be checked against original publications before financial, regulatory, or institutional decisions.

---

**FraudPulse — Turning RBI publications into actionable financial-risk intelligence.**
