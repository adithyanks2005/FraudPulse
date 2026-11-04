# Dataset

The catalogue is an HTML index, not a report. One official one-page press release PDF is available as an initial sample, but it is not the full Financial Stability Report and does not count toward the 50-page minimum. Full report PDFs are still needed.

| File | Source URL | Pages | Licence / terms | Downloaded on |
|---|---|---:|---|---|
| `data/raw/FsReports.aspx` (HTML catalogue; not a report) | [RBI Financial Stability Reports](https://rbi.org.in/Scripts/FsReports.aspx) | Not applicable | RBI public website; verify reuse terms before redistribution | 2026-11-03 |
| `data/raw/financial_Stability_june302026.pdf` (press release, not the full report) | [RBI press release 2026-2027/572](https://rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=63050) | 1 | RBI public publication; verify reuse terms before redistribution | 2026-11-04 |

The initial sample copy is `data/sample/RBI_FSR_June_2026_press_release.pdf`. It is only a one-page release announcement, not a representative sample of the full report corpus. Full report PDFs should live in `data/raw/` (not committed); replace or supplement the sample with 2–3 representative report files after collecting them.

The saved catalogue's release announcements can be extracted to `data/fsr_releases.csv` with `python app/Tools/extract_fsr_releases.py`. These are press-release links, not direct links to the full reports.
