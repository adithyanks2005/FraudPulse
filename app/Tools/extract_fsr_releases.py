"""Extract Financial Stability Report release links from the saved RBI catalogue."""

import argparse
import csv
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

BASE_URL = "https://rbi.org.in/Scripts/FsReports.aspx"


class ReleaseParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_date = False
        self._date_text: list[str] = []
        self._in_release_link = False
        self._link_href = ""
        self._link_text: list[str] = []
        self.releases: list[tuple[str, str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "b":
            self._in_date = True
            self._date_text = []
        elif tag == "a":
            href = attributes.get("href") or ""
            if "BS_PressReleaseDisplay.aspx?prid=" in href:
                self._in_release_link = True
                self._link_href = href
                self._link_text = []

    def handle_data(self, data: str) -> None:
        if self._in_date:
            self._date_text.append(data)
        if self._in_release_link:
            self._link_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "b":
            self._in_date = False
        elif tag == "a" and self._in_release_link:
            release_date = datetime.strptime("".join(self._date_text).strip(), "%b %d, %Y").date()
            title = " ".join("".join(self._link_text).split())
            self.releases.append((release_date.isoformat(), title, urljoin(BASE_URL, self._link_href)))
            self._in_release_link = False


def extract_releases(source: Path, destination: Path) -> int:
    parser = ReleaseParser()
    parser.feed(source.read_text(encoding="utf-8", errors="replace"))
    if not parser.releases:
        raise ValueError(f"No FSR press-release links found in {source}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(["release_date", "title", "source_url"])
        writer.writerows(parser.releases)
    return len(parser.releases)


def main() -> None:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=Path("data/raw/FsReports.aspx"),
        help="Saved RBI Financial Stability Reports catalogue",
    )
    argument_parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/fsr_releases.csv"),
        help="CSV file to write",
    )
    args = argument_parser.parse_args()
    count = extract_releases(args.source, args.output)
    print(f"Extracted {count} release links to {args.output}")


if __name__ == "__main__":
    main()
