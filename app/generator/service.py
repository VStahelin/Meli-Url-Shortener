import logging
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.cache import redis_client
from app.generator.exeception import ShortenUrlDeletionFailed
from app.generator.models import UrlShorted
from app.settings import CACHE_DEFAULT_TIMEOUT, BASE_URL
import string
import secrets

ALPHANUMERIC_CHARS = string.ascii_letters + string.digits

logger = logging.getLogger(__name__)


async def generate_url_token(url: str, db: AsyncSession) -> str:
    """
    Generates a unique token.
    - 6 alphanumeric characters
    - Stores the token and URL in the database
    - Caches the token and URL in Redis
    - Returns the full shortened URL

    Args:
        url (str): The original URL to shorten.
        db (AsyncSession): The database session.

    Returns:
        str: The shortened URL.
    Raises:
        Exception: If the maximum number of retries is exceeded while generating a unique token.
    """

    async def _generate_token(retries=0) -> str:
        if retries >= 5:
            raise Exception("Max retries exceeded while generating unique token.")

        new_token = "".join(
            secrets.choice(ALPHANUMERIC_CHARS) for _ in range(6)
        ).upper()

        new_entry = UrlShorted(id=new_token, url=url)
        db.add(new_entry)

        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            return await _generate_token(retries + 1)

        return new_token

    token = await _generate_token()
    redis_client.set(token, url, ex=CACHE_DEFAULT_TIMEOUT)
    return f"{BASE_URL}/{token}"


async def retrieve_url(token: str, db: AsyncSession) -> str | None:
    """
    Retrieves the original URL from the token using ORM.

    Args:
        token (str): The token to look up.
        db (AsyncSession): The database session.
    Returns:
        str | None: The original URL if found, otherwise None.
    Caches the result in Redis for faster access.
    """

    if url_cached := redis_client.get(token):
        return url_cached

    result = await db.execute(select(UrlShorted.url).where(UrlShorted.id == token))
    url = result.scalar_one_or_none()

    if url is None:
        return None

    redis_client.set(token, url, ex=CACHE_DEFAULT_TIMEOUT)
    return url


async def delete_url_token(token: str, db: AsyncSession) -> None:
    """
    Deletes the URL from the database and cache.

    Args:
        token (str): The token to delete.
        db (AsyncSession): The database session.

    Raises:
        ShortenUrlDeletionFailed: If the deletion from the database fails.
    """

    redis_client.delete(token)
    stmt = delete(UrlShorted).where(UrlShorted.id == token)

    try:
        await db.execute(stmt)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Failed to delete URL from database: {e}")
        raise ShortenUrlDeletionFailed("Failed to delete URL from database") from e
