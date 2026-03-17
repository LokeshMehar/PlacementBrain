import os

from services.ingestion.pdf_loader import load_pdf
from services.ingestion.excel_loader import load_excel
from services.ingestion.code_loader import load_code
from services.ingestion.markdown_loader import load_markdown
from services.ingestion.text_loader import load_text


# Extension to loader mapping
EXTENSION_MAP = {
    ".pdf": "pdf",
    ".xlsx": "excel",
    ".xls": "excel",
    ".py": "code",
    ".js": "code",
    ".ts": "code",
    ".java": "code",
    ".cpp": "code",
    ".hpp": "code",
    ".h": "code",
    ".html": "code",
    ".css": "code",
    ".md": "markdown",
    ".txt": "text",
    ".json": "text",
}

LOADER_MAP = {
    "pdf": load_pdf,
    "excel": load_excel,
    "code": load_code,
    "markdown": load_markdown,
    "text": load_text,
}


def dispatch(file_path: str, source_id: str, filename: str, source_type: str = None) -> list[dict]:
    """Route a file to the correct loader based on source_type or file extension."""
    if not source_type:
        ext = os.path.splitext(filename)[1].lower()
        source_type = EXTENSION_MAP.get(ext, "text")

    loader = LOADER_MAP.get(source_type, load_text)
    return loader(file_path, source_id, filename)
