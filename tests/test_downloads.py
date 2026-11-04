import csv
from urllib.error import HTTPError, URLError

from app.Tools import downloads


class FakeResponse:
    status = 200

    def __init__(self, content):
        self.content = content

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return self.content


def test_url_validation_and_filename_sanitizing():
    assert downloads.is_valid_http_url("https://example.com/report.pdf")
    assert downloads.is_valid_http_url("http://example.com:8080/report.pdf")
    assert not downloads.is_valid_http_url("ftp://example.com/report.pdf")
    assert not downloads.is_valid_http_url("https://user:pass@example.com/report.pdf")
    assert not downloads.is_valid_http_url("https://example.com:99999/report.pdf")
    assert downloads.name_for("https://example.com/%2e%2e%2freport.pdf") == "report.pdf"
    assert downloads.name_for("https://example.com/") == "index.pdf"


def test_allowed_fails_closed_when_robots_cannot_be_read(monkeypatch, capsys):
    monkeypatch.setattr(downloads, "robots", {})

    def fail_request(*_args, **_kwargs):
        raise URLError("unavailable")

    monkeypatch.setattr(downloads, "urlopen", fail_request)

    assert not downloads.allowed("https://example.com/report.pdf")
    assert "could not read robots.txt" in capsys.readouterr().out


def test_fetch_pdf_retries_transient_http_error(monkeypatch):
    calls = []

    def request(_request, timeout):
        assert timeout == downloads.TIMEOUT
        calls.append(True)
        if len(calls) == 1:
            raise HTTPError("https://example.com/report.pdf", 503, "busy", {}, None)
        return FakeResponse(b"%PDF-1.7\nreport")

    monkeypatch.setattr(downloads, "urlopen", request)
    monkeypatch.setattr(downloads.time, "sleep", lambda _seconds: None)

    assert downloads._fetch_pdf("https://example.com/report.pdf") == b"%PDF-1.7\nreport"
    assert len(calls) == 2


def test_main_saves_pdf_atomically_and_records_full_hash(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    manifest = tmp_path / "manifest.csv"
    url = "https://example.com/report.pdf"
    url_list = tmp_path / "urls.txt"
    url_list.write_text(f"# comment\n{url}\n{url}\n", encoding="utf-8")

    monkeypatch.setattr(downloads, "RAW", raw_dir)
    monkeypatch.setattr(downloads, "MANIFEST", manifest)
    monkeypatch.setattr(downloads, "robots", {})
    monkeypatch.setattr(downloads, "allowed", lambda _url: True)
    monkeypatch.setattr(downloads, "urlopen", lambda *_args, **_kwargs: FakeResponse(b"%PDF-1.7\nreport"))
    monkeypatch.setattr(downloads.time, "sleep", lambda _seconds: None)

    downloads.main(str(url_list))

    saved_file = raw_dir / "report.pdf"
    assert saved_file.read_bytes() == b"%PDF-1.7\nreport"
    assert not list(raw_dir.glob("*.tmp"))
    with manifest.open(newline="", encoding="utf-8") as mf:
        rows = list(csv.DictReader(mf))
    assert len(rows) == 1
    assert rows[0]["source_url"] == url
    assert len(rows[0]["sha256"]) == 64


def test_fetch_pdf_rejects_non_pdf_response(monkeypatch):
    monkeypatch.setattr(
        downloads,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse(b"<html>not a PDF</html>"),
    )

    assert downloads._fetch_pdf("https://example.com/report.pdf") is None
