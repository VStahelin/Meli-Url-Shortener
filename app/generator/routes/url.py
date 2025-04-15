from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.generator.schema import (
    GeneratorRequest,
    StandardResponse,
    ShortenedURLResponse,
    DeleteURLResponse,
)
from app.generator.service import generate_url_token, retrieve_url, delete_url_token
from app.generator.utils import is_safe_url_path, encode_url, decode_url
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["url"])


@router.get("/{url_id}", response_class=RedirectResponse, status_code=302)
def get_url(url_id: str):
    """
    Retrieves the original URL associated with the given token and redirects to it.

    Args:
        url_id (str): The token of the shortened URL.

    Returns:
        RedirectResponse: A 302 redirect to the original URL.

    Raises:
        HTTPException: If the token is unsafe or the URL is not found.
    """
    if not is_safe_url_path(url_id):
        raise HTTPException(status_code=400, detail="Unsafe URL provided")

    if url := retrieve_url(url_id):
        return decode_url(url)

    raise HTTPException(status_code=404, detail="URL not found")


@router.post("/", response_model=StandardResponse[ShortenedURLResponse])
def generate_url(data: GeneratorRequest) -> dict:
    """
    Generates a shortened URL token for the provided URL.

    Args:
        data (GeneratorRequest): The request payload containing the URL to shorten.
            eg: {"url":"https://www.google.com/"}

    Returns:
        dict: A dictionary containing the generated token.
    """
    try:
        received_url = encode_url(data.url)
        return {"success": True, "data": {"url": generate_url_token(received_url)}}
    except ValueError as e:
        logger.warning(f"URL invalid data {data.url} — {e}")
        return {"success": False, "message": "Invalid URL format"}


@router.delete("/{url_id}", response_model=StandardResponse[DeleteURLResponse])
def delete_url(url_id: str):
    """
    Deletes a shortened URL by its token.

    Args:
        url_id (str): The token of the shortened URL to delete.

    Returns:
        dict: A message indicating the deletion was successful.
    """
    try:
        if not is_safe_url_path(url_id):
            return {"success": False, "message": "Unsafe URL"}

        delete_url_token(url_id)
        return {"success": True, "data": {"message": "URL deleted successfully"}}
    except Exception as e:
        logger.error(f"Failed to delete token '{url_id}': {e}")
        return {"success": False, "message": "Failed to delete URL"}
