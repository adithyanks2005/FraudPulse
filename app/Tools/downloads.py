"""Polite, resumable downloader for the FraudPulse RBI document corpus.

Usage (from the repository root):
    python app/Tools/downloads.py app/Tools/url.txt

The URL list contains one URL per line; blank lines and lines beginning with
'#' are ignored. Only PDF responses are saved. Files are written atomically to
data/raw/, and successful downloads are recorded in data/manifest.csv.
"""

from __future__ import annotations

import csv
import hashlib
import os
import re
import socket
import sys
import time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

RAW_DIR = Path("data/raw")
MANIFEST_PATH = Path("data/manifest.csv")
MANIFEST_FIELDS = ["file", "source_url", "downloaded_on", "bytes", "sha256"]

HEADERS = {
    "User-Agent": (
        "FraudPulse/1.0 (RBI research downloader; "
        "contact: ksadithyan2021@gmail.com)"
    )
}
DELAY_SECONDS = 2
TIMEOUT_SECONDS = 30
MAX_ATTEMPTS = 3
CHUNK_SIZE = 1024 * 64

# Cache robots.txt results per host so it is fetched only once per run.
_robots_cache: dict[str, RobotFileParser | None] = {}


def is_valid_http_url(url: str) -> bool:
    """Return whether URL has a valid HTTP(S) scheme and hostname."""
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_allowed_by_robots(url: str) -> bool:
    """Respect robots.txt. If it cannot be fetched, fail closed."""
    parsed = urlparse(url)
    root = f"{parsed.scheme}://{parsed.netloc}"

    if root not in _robots_cache:
        parser = RobotFileParser()
        parser.set_url(f"{root}/robots.txt")
        try:
            parser.read()
            _robots_cache[root] = parser
        except (OSError, TimeoutError, URLError):
            # Do not crawl a host when its robots policy cannot be checked.
            _robots_cache[root] = None

    parser = _robots_cache[root]
    if parser is None:
        print(f"SKIP (could not read robots.txt): {url}")
        return False

    return parser.can_fetch(HEADERS["User-Agent"], url)


def filename_for(url: str) -> str:
    """Create a safe filename from the URL path."""
    raw_name = unquote(Path(urlparse(url).path).name) or "document.pdf"
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", raw_name).strip("._")
    if not safe_name:
        safe_name = "document.pdf"
    if not safe_name.lower().endswith(".pdf"):
        safe_name += ".pdf"
    return safe_name[:160]


def load_manifest() -> tuple[set[str], set[str]]:
    """Return source URLs already logged and filenames already recorded."""
    if not MANIFEST_PATH.exists():
        return set(), set()

    with MANIFEST_PATH.open("r", newline="", encoding="utf-8") as manifest_file:
        reader = csv.DictReader(manifest_file)
        if not reader.fieldnames or not set(MANIFEST_FIELDS).issubset(reader.fieldnames):
            raise ValueError(
                f"{MANIFEST_PATH} has an unexpected header. "
                f"Expected: {', '.join(MANIFEST_FIELDS)}"
            )
        rows = list(reader)

    return (
        {row["source_url"] for row in rows if row.get("source_url")},
        {row["file"] for row in rows if row.get("file")},
    )


def download_pdf(url: str, destination: Path) -> tuple[int, str]:
    """Download a PDF with retries, streaming, validation, and atomic replace."""
    temporary_path = destination.with_name(destination.name + ".part")
    last_error: Exception | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        request = Request(url, headers=HEADERS)
        digest = hashlib.sha256()
        total_bytes = 0
        first_bytes = b""

        try:
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                status = getattr(response, "status", 200)
                if status != 200:
                    raise RuntimeError(f"HTTP status {status}")

                content_type = response.headers.get_content_type().lower()
                with temporary_path.open("wb") as output:
                    while True:
                        chunk = response.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        if len(first_bytes) < 1024:
                            first_bytes += chunk[: 1024 - len(first_bytes)]
                        output.write(chunk)
                        digest.update(chunk)
                        total_bytes += len(chunk)

            # A URL may return an HTML landing page rather than a PDF.
            if b"%PDF-" not in first_bytes:
                raise ValueError(
                    f"Response is not a PDF (received {content_type}); "
                    "use the direct PDF download URL"
                )

            if total_bytes == 0:
                raise ValueError("Downloaded file is empty")

            os.replace(temporary_path, destination)
            return total_bytes, digest.hexdigest()

        except (HTTPError, URLError, TimeoutError, socket.timeout, OSError, ValueError, RuntimeError) as exc:
            last_error = exc
            temporary_path.unlink(missing_ok=True)
            if attempt < MAX_ATTEMPTS:
                wait = DELAY_SECONDS * attempt
                print(
                    f"RETRY {attempt}/{MAX_ATTEMPTS - 1} in {wait}s: "
                    f"{url} ({exc})"
                )
                time.sleep(wait)

    raise RuntimeError(f"Download failed after {MAX_ATTEMPTS} attempts: {last_error}")


def main(list_file: str) -> int:
    """Download all allowed PDF URLs from a newline-delimited list."""
    url_file = Path(list_file)
    if not url_file.is_file():
        print(f"ERROR: URL list not found: {url_file}", file=sys.stderr)
        return 2

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    logged_urls, logged_files = load_manifest()
    manifest_is_new = not MANIFEST_PATH.exists()

    downloaded = 0
    skipped = 0
    failed = 0

    with url_file.open("r", encoding="utf-8") as source_file, MANIFEST_PATH.open(
        "a", newline="", encoding="utf-8"
    ) as manifest_file:
        writer = csv.DictWriter(manifest_file, fieldnames=MANIFEST_FIELDS)
        if manifest_is_new:
            writer.writeheader()

        urls = [line.strip() for line in source_file]

        for url in urls:
            if not url or url.startswith("#"):
                continue

            if not is_valid_http_url(url):
                print(f"SKIP (invalid HTTP(S) URL): {url}")
                skipped += 1
                continue

            if url in logged_urls:
                print(f"SKIP (already recorded): {url}")
                skipped += 1
                continue

            if not is_allowed_by_robots(url):
                skipped += 1
                continue

            filename = filename_for(url)
            destination = RAW_DIR / filename

            # Avoid overwriting a different document with the same basename.
            if filename in logged_files or destination.exists():
                url_suffix = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
                destination = RAW_DIR / f"{destination.stem}-{url_suffix}.pdf"

            try:
                size, full_hash = download_pdf(url, destination)
                writer.writerow(
                    {
                        "file": destination.as_posix(),
                        "source_url": url,
                        "downloaded_on": date.today().isoformat(),
                        "bytes": size,
                        "sha256": full_hash,
                    }
                )
                manifest_file.flush()
                logged_urls.add(url)
                logged_files.add(destination.name)
                downloaded += 1
                print(
                    f"SAVED {destination} | {size:,} bytes | "
                    f"sha256={full_hash}"
                )
            except (RuntimeError, OSError, ValueError) as exc:
                failed += 1
                print(f"FAILED: {url} ({exc})", file=sys.stderr)
            finally:
                # Keep a pause between requests to RBI servers.
                time.sleep(DELAY_SECONDS)

    print(
        f"\nFinished: {downloaded} downloaded, "
        f"{skipped} skipped, {failed} failed."
    )
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage: python app/Tools/downloads.py <urls.txt>",
            file=sys.stderr,
        )
        raise SystemExit(2)

    raise SystemExit(main(sys.argv[1]))
