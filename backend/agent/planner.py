def create_plan(context, analysis):
    """
    Creates a structured implementation plan from
    the Context Engine and Analyzer results.

    Later, an AI model will generate more intelligent plans.
    """

    plan_steps = []

    query = context.get("query")
    code = context.get("code")
    error = context.get("error")

    findings = analysis.get("findings", [])

    # Step 1: Understand the affected area
    affected_area = "Unknown"

    for finding in findings:
        if finding.get("type") == "affected_area":
            affected_area = finding.get("message")

    plan_steps.append({
        "step": 1,
        "action": "Inspect affected code",
        "details": affected_area
    })

    # Step 2: Understand the error
    if error:
        plan_steps.append({
            "step": 2,
            "action": "Identify root cause",
            "details": error
        })

    # Step 3: Define the change
    plan_steps.append({
        "step": 3,
        "action": "Design the required code change",
        "details": (
            "Determine the smallest safe modification that "
            "solves the identified problem."
        )
    })

    # Step 4: Preserve existing behavior
    plan_steps.append({
        "step": 4,
        "action": "Preserve existing functionality",
        "details": (
            "Avoid unrelated changes and maintain the current "
            "API behavior."
        )
    })

    # Step 5: Validation
    plan_steps.append({
        "step": 5,
        "action": "Validate the implementation",
        "details": (
            "Run syntax checks and relevant tests after "
            "the change is implemented."
        )
    })

    return {
        "query": query,
        "affected_area": affected_area,
        "steps": plan_steps,
        "status": "plan_created"
    }