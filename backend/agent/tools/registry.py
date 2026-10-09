import inspect

from agent.tools.files import (
    list_files,
    read_file,
    write_file,
    create_file,
    modify_file,
    delete_file,
)
from agent.tools.terminal import run_command
from agent.tools.validator import validate_code
from agent.tools.search import search_project


TOOLS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "create_file": create_file,
    "modify_file": modify_file,
    "delete_file": delete_file,
    "run_command": run_command,
    "validate_code": validate_code,
    "search_project": search_project,
}


def execute_tool(
    tool_name: str,
    arguments: dict | None = None,
):
    """Execute a registered Devora tool."""
    if tool_name not in TOOLS:
        return {
            "success": False,
            "tool": tool_name,
            "error": f"Unknown tool: {tool_name}",
        }

    if arguments is None:
        arguments = {}

    if not isinstance(arguments, dict):
        return {
            "success": False,
            "tool": tool_name,
            "error": "Arguments must be a dictionary.",
        }

    tool = TOOLS[tool_name]

    try:
        signature = inspect.signature(tool)
        allowed = set(signature.parameters)
        unexpected = set(arguments) - allowed

        # Ignore unexpected arguments or filter to allowed
        valid_kwargs = {k: v for k, v in arguments.items() if k in allowed}

        result = tool(**valid_kwargs)

        return {
            "success": True,
            "tool": tool_name,
            "result": result,
        }

    except Exception as error:
        return {
            "success": False,
            "tool": tool_name,
            "error": f"{type(error).__name__}: {error}",
        }
