def truncate_string(s: str, max_length: int) -> str:
    """Truncate a string to a specified maximum length, adding ellipsis if truncated."""
    if len(s) <= max_length:
        return s
    return s[:max_length - 3] + "..."
