# Dataset

FraudPulse indexes official publications released by the Reserve Bank of India (RBI), focusing on financial stability assessments, fraud statistics, digital payments, and cybersecurity resilience.

The **Week 1 collection milestone (50+ pages)** is fulfilled and documented below with 171 pages in the primary Financial Stability Report corpus.

| File | Source URL | Pages | Licence / terms | Downloaded on |
|---|---|---:|---|---|
| `data/raw/RBI_Financial_Stability_Report_June_2025.pdf` | [RBI FSR June 2025](https://rbidocs.rbi.org.in/rdocs/PublicationReport/Pdfs/0FSRJUNE20253006258AE798B4484642AD861CC35BC2CB3D8E.PDF) | 171 | RBI public publication; verify reuse terms before redistribution | 2026-11-04 |
| `data/raw/financial_Stability_june302026.pdf` | [RBI press release 2026-2027/572](https://rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=63050) | 1 | RBI public publication; verify reuse terms before redistribution | 2026-11-04 |
| `data/raw/FsReports.aspx` (catalogue index) | [RBI Financial Stability Reports](https://rbi.org.in/Scripts/FsReports.aspx) | N/A | RBI public website; verify reuse terms before redistribution | 2026-11-03 |

## Committed Samples

Samples committed under version control for reproducibility:
* `data/sample/RBI_FSR_June_2025_sample.pdf` — 5-page representative excerpt from the June 2025 Financial Stability Report including front matter, executive overview, and financial system risk analysis.
* `data/sample/RBI_FSR_June_2026_press_release.pdf` — 1-page official release announcement.

## Inventory & Checksums

All raw files are inventoried in [`data/manifest.csv`](data/manifest.csv) with download date, byte size, and full SHA-256 hash.

## Collection Workflow

Direct publication URLs can be added to `app/Tools/url.txt` and fetched using:
```bash
python app/Tools/downloads.py app/Tools/url.txt
```
The download tool respects `robots.txt`, implements rate limits, retries transient failures, validates PDF headers, and writes records atomically to `data/manifest.csv`.
