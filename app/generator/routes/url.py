from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.generator.schema import (
    GeneratorRequest,
    StandardResponse,
    ShortenedURLResponse,
    DeleteURLResponse,
)
from app.generator.service import generate_url_token, retrieve_url, delete_url_token
from app.generator.utils import (
    is_safe_url_path,
    validate_url_scheme,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["url"])


@router.get("/{url_id}", response_class=RedirectResponse, status_code=302)
async def get_url(url_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves the original URL associated with the given token and redirects to it.

    Args:
        url_id (str): The token of the shortened URL.
        db (AsyncSession): The database session.

    Returns:
        RedirectResponse: A 302 redirect to the original URL.

    Raises:
        HTTPException: If the token is unsafe or the URL is not found.
    """
    if not is_safe_url_path(url_id):
        raise HTTPException(status_code=400, detail="Unsafe URL provided")

    if url := await retrieve_url(url_id, db):
        return url

    raise HTTPException(status_code=404, detail="URL not found")


@router.post("/", response_model=StandardResponse[ShortenedURLResponse])
async def generate_url(
    data: GeneratorRequest, db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Generates a shortened URL token for the provided URL.

    Args:
        data (GeneratorRequest): The request payload containing the URL to shorten.
            eg: {"url":"https://www.google.com/"}
        db (AsyncSession): The database session.

    Returns:
        dict: A dictionary containing the generated token.
    """
    try:
        received_url = validate_url_scheme(data.url)
        shortened_url = await generate_url_token(received_url, db)
        return {"success": True, "data": {"url": shortened_url}}
    except ValueError as e:
        logger.warning(f"URL invalid data {data.url} — {e}")
        return {"success": False, "message": "Invalid URL format"}


@router.delete("/{url_id}", response_model=StandardResponse[DeleteURLResponse])
async def delete_url(url_id: str, db: AsyncSession = Depends(get_db)):
    """
    Deletes a shortened URL by its token.

    Args:
        url_id (str): The token of the shortened URL to delete.
        db (AsyncSession): The database session.

    Returns:
        dict: A message indicating the deletion was successful.
    """
    try:
        if not is_safe_url_path(url_id):
            return {"success": False, "message": "Unsafe URL"}

        await delete_url_token(url_id, db)
        return {"success": True, "data": {"message": "URL deleted successfully"}}
    except Exception as e:
        logger.error(f"Failed to delete token '{url_id}': {e}")
        return {"success": False, "message": "Failed to delete URL"}
