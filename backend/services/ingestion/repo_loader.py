import os
import shutil
import tempfile

from git import Repo

from services.ingestion.code_loader import load_code
from services.ingestion.markdown_loader import load_markdown
from services.ingestion.text_loader import load_text


# File extensions to process
CODE_EXTENSIONS = {".py", ".js", ".ts", ".java", ".cpp", ".hpp", ".c", ".h", ".html", ".css"}
MARKDOWN_EXTENSIONS = {".md"}
TEXT_EXTENSIONS = {".txt", ".json"}
ALLOWED_EXTENSIONS = CODE_EXTENSIONS | MARKDOWN_EXTENSIONS | TEXT_EXTENSIONS

# Directories to skip
SKIP_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv", "env", "dist", "build"}

# Max lines per file
MAX_LINES = 500


def _normalize_repo_url(url: str) -> str:
    import re
    # Remove /tree/... or /blob/... from github URLs to get base repo
    match = re.match(r"(https?://github\.com/[^/]+/[^/]+?)(?:/(?:tree|blob)/.*)?$", url)
    if match:
        base_url = match.group(1)
        if base_url.endswith(".git"):
            return base_url
        return base_url
    return url

def load_repo(repo_url: str, source_id: str) -> list[dict]:
    """Clone a git repo and process all supported files."""
    clone_dir = os.path.join(tempfile.gettempdir(), source_id)
    chunks = []
    
    clean_url = _normalize_repo_url(repo_url)

    try:
        # Clone the repository
        Repo.clone_from(clean_url, clone_dir, depth=1)

        # Walk all files
        for root, dirs, files in os.walk(clone_dir):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in ALLOWED_EXTENSIONS:
                    continue

                file_path = os.path.join(root, fname)
                rel_path = os.path.relpath(file_path, clone_dir)

                # Skip files that are too long
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        line_count = sum(1 for _ in f)
                    if line_count > MAX_LINES:
                        continue
                except Exception:
                    continue

                # Route to appropriate loader
                try:
                    if ext in CODE_EXTENSIONS:
                        file_chunks = load_code(file_path, source_id, rel_path)
                    elif ext in MARKDOWN_EXTENSIONS:
                        file_chunks = load_markdown(file_path, source_id, rel_path)
                    else:
                        file_chunks = load_text(file_path, source_id, rel_path)

                    # Add repo_url to metadata
                    for chunk in file_chunks:
                        chunk["metadata"]["repo_url"] = repo_url
                        chunk["metadata"]["source_type"] = "repo"

                    chunks.extend(file_chunks)
                except Exception:
                    continue  # Skip files that fail to process

    finally:
        # Cleanup cloned repo
        if os.path.exists(clone_dir):
            shutil.rmtree(clone_dir, ignore_errors=True)

    return chunks
