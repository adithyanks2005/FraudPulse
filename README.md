# FraudPulse

> Track RBI-reported bank frauds, cyber incidents, and digital-payment risks with current, cited evidence.

## Problem

Fraud and cyber-risk trends are scattered across RBI Annual Reports, half-yearly Financial Stability Reports (FSRs), and payment-system chapters. Each report is published on a different schedule, so quarterly board notes can easily quote outdated figures. FraudPulse keeps the relevant RBI evidence searchable and current, including passages added in newly published reports.

## Who it is for

IT-risk officers at urban co-operative banks, such as an officer in Tiruchirappalli preparing a quarterly cyber-risk note for the board.

## Signature feature

A "What's new since your last note?" view lists RBI fraud and cyber-risk passages added since a selected date.

## Hardest problem (my interview story)

Freshness without reprocessing the full corpus: a daily job checks RBI publication pages, hashes each PDF, and re-indexes only new or changed chapters. This makes a newly issued FSR searchable within an hour without re-embedding more than 6,000 pages. The project measures the re-indexing time and cost for one newly published report.

## Dataset

| Source | Link | Documents | Pages | Licence / terms |
|---|---|---:|---:|---|
| RBI Annual Reports | [RBI publications](https://rbi.org.in/Scripts/FsReports.aspx) | 10 years, chapter-wise PDFs | Included in 6,000+ page corpus | RBI public publications; verify reuse terms before redistribution |
| RBI Financial Stability Reports | [RBI Financial Stability Reports](https://rbi.org.in/Scripts/FsReports.aspx) | Half-yearly, 10 years | Included in 6,000+ page corpus | RBI public publications; verify reuse terms before redistribution |

Minimum corpus: 30 reports and 6,000+ pages from RBI publications.

## Research agent

The research agent drafts the quarterly board note by querying FraudPulse for card fraud, digital-payment fraud, and cyber incidents, then uses a calculator for year-on-year changes. A fact-checking step confirms that each reported figure comes from the latest available RBI publication before the officer signs the note.

## 10 real questions

1. How many digital payment frauds did banks report last year according to the RBI Annual Report?
2. What did the December 2025 Financial Stability Report say about a financial sector cybersecurity strategy?
3. How has the share of card and internet frauds in total fraud cases changed over five years?

## Success criteria

- A new RBI report is searchable within 60 minutes of publication.
- Each update re-indexes under 5% of total chunks.
- Re-indexing time and cost are measured for one new report.

## Run it

```bash
uv python install 3.12
uv venv --python 3.12
uv sync --group dev
cp .env.example .env                                 # Windows: copy .env.example .env
uv run uvicorn app.main:app --reload
curl localhost:8000/health
```

This project intentionally supports Python 3.12 through 3.14. Python 3.15 can force a source build of PyYAML through `uvicorn[standard]`; use the 3.12 environment above rather than `--frozen`, which would retain an unusable environment.

## Live link

<Added in Week 2>
