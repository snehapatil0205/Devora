def review_implementation(code: str, validation: dict):
    """
    Reviews the implementation after validation.
    """

    findings = []

    if not code or not code.strip():
        return {
            "status": "failed",
            "summary": "No implementation was available for review.",
            "findings": []
        }

    if validation.get("status") != "passed":
        return {
            "status": "failed",
            "summary": "Implementation review skipped because validation failed.",
            "findings": []
        }

    # Basic review checks
    if "FastAPI" in code:
        findings.append({
            "type": "framework",
            "status": "passed",
            "message": "FastAPI implementation detected."
        })

    if "def " in code:
        findings.append({
            "type": "structure",
            "status": "passed",
            "message": "Function-based code structure detected."
        })

    if "return" in code:
        findings.append({
            "type": "implementation",
            "status": "passed",
            "message": "Implementation contains a return statement."
        })

    return {
        "status": "passed",
        "summary": "Implementation passed the basic code review.",
        "findings": findings
    }