def analyze_context(context):
    """
    Analyzes the structured context produced by the Context Engine.

    This is currently a rule-based analyzer.
    Later, an AI model will perform the deeper analysis.
    """

    query = context.get("query")
    code = context.get("code")
    error = context.get("error")
    input_type = context.get("input_type")

    findings = []

    # Analyze explicit error
    if error:
        findings.append({
            "type": "error",
            "message": error,
            "source": "user_provided_error"
        })

    # Basic code analysis
    if code:
        if "NameError" in str(error):
            findings.append({
                "type": "root_cause",
                "message": "The code appears to reference a variable or name that has not been defined.",
                "source": "code_and_error_analysis"
            })

        if "def login" in code:
            findings.append({
                "type": "affected_area",
                "message": "The login function is the primary affected area.",
                "source": "code_analysis"
            })

    # Determine severity
    severity = "low"

    if error:
        severity = "high"

    return {
        "input_type": input_type,
        "query": query,
        "findings": findings,
        "severity": severity,
        "status": "analysis_complete"
    }