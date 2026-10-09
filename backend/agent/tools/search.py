from pathlib import Path

from agent.tools.files import WORKSPACE


def search_project(query: str):
    """
    Search for a text string across files inside Devora's
    controlled workspace.
    """

    query = query.strip()

    if not query:
        raise ValueError("Search query cannot be empty.")

    if not WORKSPACE.exists():
        return {
            "query": query,
            "matches": []
        }

    matches = []

    for file_path in WORKSPACE.rglob("*"):

        if not file_path.is_file():
            continue

        try:
            content = file_path.read_text(
                encoding="utf-8"
            )
        except (UnicodeDecodeError, OSError):
            # Ignore files that cannot be read as text.
            continue

        lines = content.splitlines()

        for line_number, line in enumerate(lines, start=1):

            if query.lower() in line.lower():

                matches.append({
                    "path": str(
                        file_path.relative_to(WORKSPACE)
                    ),
                    "line": line_number,
                    "content": line.strip()
                })

    return {
        "query": query,
        "matches": matches,
        "count": len(matches)
    }