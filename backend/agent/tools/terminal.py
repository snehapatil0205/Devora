import subprocess

from pathlib import Path

from agent.tools.files import WORKSPACE


# Commands that Devora is allowed to execute.
ALLOWED_COMMANDS = {
    "python",
    "pip",
    "pytest",
    "npm",
    "node",
}


def run_command(command: str):
    """
    Execute an allowed command from Devora's controlled workspace.
    """

    command = command.strip()

    if not command:
        raise ValueError("Command cannot be empty.")

    # Get the first word of the command.
    command_name = command.split()[0].lower()

    # Handle Windows paths such as python.exe.
    command_name = Path(command_name).stem

    if command_name not in ALLOWED_COMMANDS:
        raise PermissionError(
            f"Command '{command_name}' is not allowed."
        )

    result = subprocess.run(
        command,
        cwd=WORKSPACE,
        shell=True,
        capture_output=True,
        text=True,
        timeout=60,
    )

    return {
        "command": command,
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "success": result.returncode == 0,
    }