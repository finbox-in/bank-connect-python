def is_valid_uuid4(value):
    from uuid import UUID
    try:
        val = UUID(value, version=4)
    except (ValueError, AttributeError):
        return False
    # also check whether valid number of hyphens are present
    return value.count('-') == 4

def check_progress(progress):
    if progress is None:
        return "not_found"
    for statement in progress:
        if statement["status"] in ["failed", "processing"]:
            return statement["status"]
    return "completed"
