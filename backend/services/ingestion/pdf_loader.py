from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_pdf(file_path: str, source_id: str, filename: str) -> list[dict]:
    """Extract text from PDF page by page and split into chunks."""
    reader = PdfReader(file_path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = []

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if not text.strip():
            continue

        page_chunks = splitter.split_text(text)
        for chunk_text in page_chunks:
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "source_id": source_id,
                    "filename": filename,
                    "source_type": "pdf",
                    "page_number": page_num,
                },
            })

    return chunks
