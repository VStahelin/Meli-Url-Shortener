import re
from urllib.parse import unquote


from urllib.parse import quote


def encode_url(url: str) -> str:
    """
    Prevents dangerous URL schemes and encodes the URL safely for storage.
    """
    if url.startswith(("javascript:", "data:")):
        raise ValueError("Invalid URL")

    return quote(url, safe="")


def decode_url(url: str) -> str:
    """
    Decodes the URL safely.
    """
    decoded_url = unquote(url)

    return decoded_url


def is_safe_url_path(path: str) -> bool:
    """
    Checks if the URL path is safe:
    - Must not contain suspicious patterns
    """

    decoded_path = unquote(path)

    if "../" in decoded_path or "./" in decoded_path:
        return False

    if not re.match(r"^[a-zA-Z0-9_\-]+$", decoded_path):
        return False

    return True
