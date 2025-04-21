import re
from urllib.parse import urlparse, unquote


def validate_url_scheme(url: str) -> str:
    """
    Validates a URL to ensure it uses a safe scheme and doesn't contain known malicious patterns.

    Args:
        url (str): The URL to validate.

    Returns:
        str: The validated URL if considered safe.

    Raises:
        ValueError: If the URL contains dangerous schemes or patterns.
    """
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(
            "URL must start with http:// or https:// and include a valid domain"
        )

    decoded = unquote(url)

    dangerous_patterns = [
        r"(<script|</script>)",  # XSS script tags
        r"javascript:\b",  # inline JS scheme
        r"vbscript:\b",  # inline VBScript
        r"data:[^,]+;base64,",  # data URI base64 injection
        r"\bunion\s+select\b",  # SQL injection UNION
        r"--|;|\bOR\b|\bAND\b",  # SQL injection operators
        r"\.\./",  # path traversal
        r"\bexec\b|\bcmd\b",  # command injection keywords
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, decoded, re.IGNORECASE):
            raise ValueError("URL contains disallowed scheme or pattern")

    return url


def is_safe_url_path(path: str) -> bool:
    """
    Validates if the provided URL token is safe.

    A safe token must:
    - Have exactly 6 characters
    - Contain only alphanumeric characters (a-z, A-Z, 0-9)

    Args:
        path (str): The token extracted from the URL path.

    Returns:
        bool: True if the token is safe, False otherwise.
    """
    return len(path) == 6 and path.isalnum()
