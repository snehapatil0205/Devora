from typing import Optional


def build_context(
    query: Optional[str] = None,
    code: Optional[str] = None,
    error: Optional[str] = None,
    project_name: Optional[str] = None,
):
    """
    Collects and structures everything provided by the user.
    This is the first stage of the Devora agent pipeline.
    """

    sources = []

    if query:
        sources.append("user_query")

    if code:
        sources.append("code")

    if error:
        sources.append("error")

    if project_name:
        sources.append("project")

    if not sources:
        input_type = "empty"
    elif "project" in sources:
        input_type = "project"
    elif "code" in sources and "error" in sources:
        input_type = "code_and_error"
    elif "code" in sources:
        input_type = "code"
    elif "error" in sources:
        input_type = "error"
    else:
        input_type = "requirement"

    return {
        "input_type": input_type,
        "sources": sources,
        "query": query,
        "code": code,
        "error": error,
        "project_name": project_name,
    }