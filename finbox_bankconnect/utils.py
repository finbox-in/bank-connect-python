def is_valid_uuid4(value):
    from uuid import UUID
    try:
        val = UUID(value, version=4)
    except (ValueError, AttributeError, TypeError):
        return False
    # also check whether valid number of hyphens are present
    return value.count('-') == 4
