import base64
import os

from sqlalchemy import text

from app.core.cache import redis_client, DEFAULT_TIMEOUT
from app.core.database import SessionLocal

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


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
        redis_client.set(token, url, ex=DEFAULT_TIMEOUT)
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

    redis_client.set(token, url, ex=DEFAULT_TIMEOUT)
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


def consolidate_access_counts() -> None:
    """
    Consolidates access counts from Redis to the database.

    This function retrieves access count statistics stored in Redis for
    shortened URLs, updates the corresponding records in the database,
    and removes the processed keys from Redis.
    """

    keys = redis_client.keys("stats:*")

    with SessionLocal() as db:
        for key in keys:
            token = key.split("stats:")[1]
            count = redis_client.getdel(key)

            if count is None:
                continue

            count = int(count)

            db.execute(
                text(
                    """
                UPDATE url_shortened
                SET access_count = access_count + :count
                WHERE id = :id
            """
                ),
                {"id": token, "count": count},
            )

        db.commit()
