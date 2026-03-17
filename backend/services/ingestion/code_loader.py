import ast
import os


def _extract_python_chunks(source: str, source_id: str, filename: str) -> list[dict]:
    """Use AST to extract each function and class as a separate chunk."""
    chunks = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Fall back to line-based chunking if parsing fails
        return _line_based_chunks(source, source_id, filename, "python")

    lines = source.splitlines(keepends=True)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start_line = node.lineno - 1
            end_line = node.end_lineno if node.end_lineno else start_line + 1

            # Include decorators
            if node.decorator_list:
                first_decorator = node.decorator_list[0]
                start_line = first_decorator.lineno - 1

            chunk_text = "".join(lines[start_line:end_line])
            if chunk_text.strip():
                func_name = node.name if hasattr(node, "name") else ""
                node_type = "class" if isinstance(node, ast.ClassDef) else "function"
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "source_id": source_id,
                        "filename": filename,
                        "source_type": "code",
                        "language": "python",
                        "function_name": func_name,
                        "node_type": node_type,
                    },
                })

    # If no functions/classes found, chunk the whole file
    if not chunks:
        return _line_based_chunks(source, source_id, filename, "python")

    return chunks


def _line_based_chunks(
    source: str, source_id: str, filename: str, language: str,
    chunk_lines: int = 50, overlap: int = 10,
) -> list[dict]:
    """Split source code into chunks by line count with overlap."""
    lines = source.splitlines()
    chunks = []
    i = 0

    while i < len(lines):
        end = min(i + chunk_lines, len(lines))
        chunk_text = "\n".join(lines[i:end])
        if chunk_text.strip():
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "source_id": source_id,
                    "filename": filename,
                    "source_type": "code",
                    "language": language,
                    "line_range": f"{i + 1}-{end}",
                },
            })
        i += chunk_lines - overlap

    return chunks


def load_code(file_path: str, source_id: str, filename: str) -> list[dict]:
    """Load code file and chunk it based on language."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()

    if not source.strip():
        return []

    ext = os.path.splitext(filename)[1].lower()

    if ext == ".py":
        return _extract_python_chunks(source, source_id, filename)

    # Language detection from extension
    lang_map = {
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".hpp": "cpp",
        ".h": "cpp",
        ".c": "c",
        ".go": "go",
        ".rs": "rust",
        ".html": "html",
        ".css": "css",
    }
    language = lang_map.get(ext, "unknown")
    return _line_based_chunks(source, source_id, filename, language)
