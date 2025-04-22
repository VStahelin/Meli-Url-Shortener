from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.dependencies import get_db
from app.generator.exeception import ShortenUrlDeletionFailed
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
        raise HTTPException(status_code=400, detail="Bad token")

    if url := await retrieve_url(url_id, db):
        return url

    raise HTTPException(status_code=404, detail="URL not found")


@router.post("/", response_model=StandardResponse[ShortenedURLResponse])
async def generate_url(
    data: GeneratorRequest, db: AsyncSession = Depends(get_db)
) -> JSONResponse:
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
        return JSONResponse(
            status_code=200,
            content={"success": True, "data": {"url": shortened_url}, "message": None},
        )
    except ValueError as e:
        logger.warning(f"URL invalid data {data.url} — {e}")
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Invalid URL", "data": None},
        )


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
    if not is_safe_url_path(url_id) or not url_id:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Bad token", "data": None},
        )

    try:
        await delete_url_token(url_id, db)
        return {"success": True, "data": {"message": "URL deleted successfully"}}

    except ShortenUrlDeletionFailed:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Could not delete the Token",
                "data": None,
            },
        )

    except Exception:
        logger.error(f"Failed to delete URL {url_id}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "data": None,
            },
        )
