import os
from pathlib import Path

# Devora's controlled workspace
WORKSPACE = (Path(__file__).resolve().parents[2] / "workspace").resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)
try:
    os.chmod(WORKSPACE, 0o755)
except Exception:
    pass

EXCLUDED_DIRS = {
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".next",
    ".nuxt",
    "dist",
    "build",
    ".cache",
    "coverage",
}

EXCLUDED_FILES = {
    ".DS_Store",
}

EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
}

MAX_LIST_ITEMS = 500


def is_excluded(path: Path) -> bool:
    """Return True for dependency, generated, or unwanted paths."""
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return True

    if path.name in EXCLUDED_FILES:
        return True

    if path.suffix in EXCLUDED_SUFFIXES:
        return True

    return False


def safe_path(path: str) -> Path:
    """Resolve a path and ensure it stays inside the workspace."""
    cleaned = path.strip().lstrip("/\\")
    root = WORKSPACE.resolve()
    target = (root / cleaned).resolve()

    try:
        target.relative_to(root)
    except ValueError:
        raise ValueError("Access outside the Devora workspace is not allowed.")

    return target


def list_files():
    """List useful workspace files without traversing excluded folders."""
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    items = []
    truncated = False

    for current_root, dirs, files in os.walk(WORKSPACE, followlinks=False):
        current = Path(current_root)

        # Filter excluded directories in-place
        dirs[:] = [
            name
            for name in dirs
            if name not in EXCLUDED_DIRS and not (current / name).is_symlink()
        ]

        for name in dirs:
            path = current / name
            try:
                relative = path.relative_to(WORKSPACE)
                items.append({
                    "type": "directory",
                    "path": relative.as_posix(),
                })
            except Exception:
                continue

            if len(items) >= MAX_LIST_ITEMS:
                truncated = True
                break

        if truncated:
            break

        for name in files:
            path = current / name

            try:
                relative = path.relative_to(WORKSPACE)
            except Exception:
                continue

            if is_excluded(relative) or path.is_symlink():
                continue

            items.append({
                "type": "file",
                "path": relative.as_posix(),
            })

            if len(items) >= MAX_LIST_ITEMS:
                truncated = True
                break

        if truncated:
            break

    return {
        "workspace": str(WORKSPACE),
        "items": items,
        "count": len(items),
        "truncated": truncated,
    }


def read_file(path: str):
    """Read a file from the controlled workspace."""
    file_path = safe_path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    return {
        "path": path,
        "content": file_path.read_text(encoding="utf-8", errors="replace"),
    }


def write_file(path: str, content: str):
    """Create or overwrite a file inside the controlled workspace."""
    file_path = safe_path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")

    return {
        "path": path,
        "success": True,
        "size": len(content),
        "message": f"File '{path}' written successfully.",
    }


def create_file(path: str, content: str):
    """Create or overwrite a workspace file (safe wrapper for write_file)."""
    return write_file(path, content)


def modify_file(path: str, content: str):
    """Modify or write an existing workspace file (safe wrapper for write_file)."""
    return write_file(path, content)


def delete_file(path: str, confirm: bool = True):
    """Delete a file from the workspace."""
    file_path = safe_path(path)

    if not file_path.exists():
        return {
            "path": path,
            "deleted": False,
            "message": f"File '{path}' does not exist.",
        }

    if file_path.is_file():
        file_path.unlink()
    elif file_path.is_dir():
        import shutil
        shutil.rmtree(file_path)

    return {
        "path": path,
        "deleted": True,
        "message": f"Deleted '{path}'.",
    }
