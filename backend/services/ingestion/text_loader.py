from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_text(file_path: str, source_id: str, filename: str) -> list[dict]:
    """Load a plain text file and split into chunks."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if not content.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    text_chunks = splitter.split_text(content)
    chunks = []

    for chunk_text in text_chunks:
        chunks.append({
            "text": chunk_text,
            "metadata": {
                "source_id": source_id,
                "filename": filename,
                "source_type": "text",
            },
        })

    return chunks
