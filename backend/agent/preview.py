def create_change_preview(context, analysis, plan):
    """
    Creates a human-readable preview of the changes
    Devora intends to make.

    No code is modified at this stage.
    """

    affected_area = plan.get("affected_area")
    steps = plan.get("steps", [])

    changes = []

    for step in steps:
        changes.append({
            "step": step["step"],
            "change": step["action"],
            "reason": step["details"]
        })

    return {
        "status": "awaiting_approval",
        "affected_area": affected_area,
        "changes": changes,
        "files_to_modify": [],
        "warning": "No code will be modified until the user approves these changes."
    }