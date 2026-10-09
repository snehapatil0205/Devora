import ast


def validate_code(code: str):
    """
    Validates Python code without executing it.
    """

    if not code or not code.strip():
        return {
            "status": "failed",
            "checks": [
                {
                    "name": "Code presence",
                    "status": "failed",
                    "message": "No code was provided."
                }
            ]
        }

    checks = []

    # Syntax validation
    try:
        ast.parse(code)

        checks.append({
            "name": "Python syntax",
            "status": "passed",
            "message": "Python syntax is valid."
        })

    except SyntaxError as error:

        checks.append({
            "name": "Python syntax",
            "status": "failed",
            "message": (
                f"Syntax error at line {error.lineno}: "
                f"{error.msg}"
            )
        })

    overall_status = "passed"

    for check in checks:
        if check["status"] == "failed":
            overall_status = "failed"

    return {
        "status": overall_status,
        "checks": checks
    }