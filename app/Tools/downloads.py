"""Polite PDF downloader: python app/Tools/downloads.py urls.txt.

The URL list contains one URL per line; blank lines and lines beginning with
'#' are ignored. PDF files are written atomically to data/raw/, and successful
downloads are recorded in data/manifest.csv.
"""
import csv
import hashlib
import os
import re
import sys
import tempfile
import time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

RAW = "data/raw"
MANIFEST = "data/manifest.csv"
HEADERS = {
    "User-Agent": (
        "ADITHYANKS/1.0 (Bastion Brief; contact:"
        "ksadithyan2021@gmail.com)"
    )
}
DELAY = 2
TIMEOUT = 30
MAX_ATTEMPTS = 3
TRANSIENT_HTTP_STATUS = {429, 500, 502, 503, 504}

robots = {}


def is_valid_http_url(url):
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme.lower() in {"http", "https"}
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and parsed.port != 0
        )
    except ValueError:
        return False


def allowed(url):
    parsed = urlparse(url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    if root not in robots:
        parser = RobotFileParser()
        parser.set_url(f"{root}/robots.txt")
        try:
            request = Request(parser.url, headers=HEADERS)
            with urlopen(request, timeout=TIMEOUT) as response:
                if response.status != 200:
                    robots[root] = None
                else:
                    content = response.read().decode("utf-8", errors="replace")
                    parser.parse(content.splitlines())
                    robots[root] = parser
        except (OSError, TimeoutError, URLError):
            robots[root] = None

    parser = robots[root]
    if parser is None:
        print(f"SKIP (could not read robots.txt): {url}")
        return False

    return parser.can_fetch(HEADERS["User-Agent"], url)


def name_for(url):
    name = unquote(urlparse(url).path).replace("\\", "/").rsplit("/", 1)[-1]
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    return name or "index.pdf"


def _logged_urls():
    if not os.path.exists(MANIFEST) or os.path.getsize(MANIFEST) == 0:
        return set()

    with open(MANIFEST, newline="", encoding="utf-8") as mf:
        return {
            row["source_url"]
            for row in csv.DictReader(mf)
            if row.get("source_url")
        }


def _fetch_pdf(url):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            request = Request(url, headers=HEADERS)
            with urlopen(request, timeout=TIMEOUT) as response:
                if response.status != 200:
                    print(f"failed {response.status} {url}")
                    return None
                content = response.read()
        except HTTPError as exc:
            if exc.code in TRANSIENT_HTTP_STATUS and attempt < MAX_ATTEMPTS:
                time.sleep(DELAY)
                continue
            print(f"failed {exc.code} {url}")
            return None
        except (URLError, TimeoutError) as exc:
            if attempt < MAX_ATTEMPTS:
                time.sleep(DELAY)
                continue
            print(f"failed {exc} {url}")
            return None

        if b"%PDF-" not in content[:1024]:
            print(f"SKIP (response is not a PDF): {url}")
            return None
        return content

    return None


def _save_atomically(path, content):
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)


def main(list_file):
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(os.path.dirname(MANIFEST) or ".", exist_ok=True)
    new_manifest = not os.path.exists(MANIFEST) or os.path.getsize(MANIFEST) == 0
    logged_urls = _logged_urls()

    with open(MANIFEST, "a", newline="", encoding="utf-8") as mf:
        log = csv.writer(mf)
        if new_manifest:
            log.writerow(
                ["file", "source_url", "downloaded_on", "bytes", "sha256"]
            )

        with open(list_file, encoding="utf-8") as fh:
            urls = [url.strip() for url in fh]

        for url in urls:
            if not url or url.startswith("#"):
                continue

            if not is_valid_http_url(url):
                print(f"SKIP (invalid HTTP(S) URL): {url}")
                continue

            if url in logged_urls:
                print(f"SKIP (already recorded): {url}")
                continue

            if not allowed(url):
                print("BLOCKED by robots.txt, not downloading:", url)
                continue

            path = Path(RAW) / name_for(url)
            if path.exists():
                print("skip (already have)", path)
                continue

            content = _fetch_pdf(url)
            if content is None:
                continue

            _save_atomically(path, content)
            digest = hashlib.sha256(content).hexdigest()
            log.writerow(
                [str(path), url, date.today().isoformat(), len(content), digest]
            )
            mf.flush()
            logged_urls.add(url)
            print("saved", path, len(content), "bytes")
            time.sleep(DELAY)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage: python app/Tools/downloads.py <url-list-file>",
            file=sys.stderr,
        )
        sys.exit(2)

    main(sys.argv[1])
