import ast

from pathlib import Path

from agent.tools.files import WORKSPACE


def validate_code(path: str):
    """
    Validate Python syntax for a file inside Devora's
    controlled workspace.
    """

    file_path = WORKSPACE / path

    # Security check
    try:
        file_path.resolve().relative_to(WORKSPACE.resolve())
    except ValueError:
        raise ValueError(
            "Access outside the Devora workspace is not allowed."
        )

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"Path is not a file: {path}"
        )

    content = file_path.read_text(
        encoding="utf-8"
    )

    extension = file_path.suffix.lower()

    # Currently support Python syntax validation.
    if extension == ".py":

        try:
            ast.parse(content)

            return {
                "path": path,
                "language": "python",
                "valid": True,
                "error": None,
            }

        except SyntaxError as e:

            return {
                "path": path,
                "language": "python",
                "valid": False,
                "error": {
                    "message": e.msg,
                    "line": e.lineno,
                    "column": e.offset,
                    "text": e.text,
                },
            }

    return {
        "path": path,
        "language": extension or "unknown",
        "valid": None,
        "error": (
            "Syntax validation for this file type "
            "is not implemented yet."
        ),
    }