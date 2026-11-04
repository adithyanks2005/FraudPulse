from pathlib import Path

import pymupdf


def parse_pdf(pdf_path: str) -> list[dict]:
    """Extract text from a PDF while preserving page numbers."""

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages = []

    with pymupdf.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text")

            pages.append({"document": pdf_path.name, "page": page_number, "text": text.strip()})

    return pages


if __name__ == "__main__":
    pdf_file = input("Enter RBI PDF path: ")

    extracted_pages = parse_pdf(pdf_file)

    print(f"\nTotal pages processed: {len(extracted_pages)}")

    for page in extracted_pages[:2]:
        print(f"\nPage {page['page']}:")
        print(page["text"][:500])
