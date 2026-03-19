import re
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_markdown(file_path: str, source_id: str, filename: str) -> list[dict]:
    """Split markdown by headings, with sub-splitting for long sections."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if not content.strip():
        return []

    # Split by headings (lines starting with #)
    sections = re.split(r"(?=^#{1,6}\s)", content, flags=re.MULTILINE)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = []

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract heading from the section
        lines = section.split("\n", 1)
        heading = lines[0].strip().lstrip("#").strip() if lines[0].startswith("#") else "Introduction"

        if len(section) > 800:
            sub_chunks = splitter.split_text(section)
            for sub in sub_chunks:
                chunks.append({
                    "text": sub,
                    "metadata": {
                        "source_id": source_id,
                        "filename": filename,
                        "source_type": "markdown",
                        "section_heading": heading,
                    },
                })
        else:
            chunks.append({
                "text": section,
                "metadata": {
                    "source_id": source_id,
                    "filename": filename,
                    "source_type": "markdown",
                    "section_heading": heading,
                },
            })

    return chunks
