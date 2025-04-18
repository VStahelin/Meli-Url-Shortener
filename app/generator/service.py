import base64
import os

from sqlalchemy import text

from app.core.cache import redis_client
from app.core.database import SessionLocal
from app.settings import CACHE_DEFAULT_TIMEOUT, BASE_URL


def generate_url_token(url: str) -> str:
    """
    Generates a unique token.
    - Base64 6 characters token
    """

    with SessionLocal() as db:

        def _generate_token() -> str:
            new_token = (
                base64.urlsafe_b64encode(os.urandom(6)).decode("utf-8").rstrip("=")
            )

            stmt = text(
                """
                INSERT INTO url_shortened (id, url)
                VALUES (:id, :url)
                ON CONFLICT DO NOTHING
            """
            )

            result = db.execute(stmt, {"id": new_token, "url": url})
            db.commit()

            if result.rowcount == 0:
                return _generate_token()

            return new_token

        token = _generate_token()
        redis_client.set(token, url, ex=CACHE_DEFAULT_TIMEOUT)
        return f"{BASE_URL}/{token}"


def retrieve_url(token: str) -> str | None:
    """
    Retrieves the original URL from the token.
    """

    if url_cached := redis_client.get(token):
        redis_client.incr(f"stats:{token}")
        return url_cached

    with SessionLocal() as db:
        stmt = text("SELECT url FROM url_shortened WHERE id = :id")
        result = db.execute(stmt, {"id": token}).fetchone()

        if result is None:
            return None

        url = result[0]

    redis_client.set(token, url, ex=CACHE_DEFAULT_TIMEOUT)
    redis_client.incr(f"stats:{token}")
    return url


def delete_url_token(token: str) -> None:
    """
    Deletes the URL from the database and cache.
    Returns True if successful, False otherwise.
    """

    redis_client.delete(token)

    with SessionLocal() as db:
        stmt = text(
            """
            DELETE FROM url_shortened WHERE id = :id
            """
        )
        db.execute(stmt, {"id": token})
        db.commit()
