import logging
import subprocess
import asyncio

from contextlib import asynccontextmanager
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.generator.routes import url, stats
from app.generator.schema import ErrorResponse
from fastapi import HTTPException

from fastapi import FastAPI, APIRouter

from app.core.cache import redis_client
from app.generator.service import (
    consolidate_access_counts,
)
from prometheus_fastapi_instrumentator import Instrumentator

logger = logging.getLogger(__name__)


app = FastAPI()
root_router = APIRouter()


instrumentator = Instrumentator().instrument(app).expose(app)

LOCK_KEY = "lock:consolidator"
LOCK_EXPIRE = 10


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Handles the lifespan of the FastAPI application.

    This function ensures that the database migrations are applied
    using Alembic before the application starts.

    Args:
        _app (FastAPI): The FastAPI application instance.
    """

    subprocess.run(["alembic", "upgrade", "head"])

    async def background_consolidator():
        while True:
            try:
                got_lock = redis_client.set(LOCK_KEY, "1", nx=True, ex=LOCK_EXPIRE)
                if got_lock:
                    consolidate_access_counts()
            except Exception as e:
                print(f"[ERROR] Consolidator failed: {e}")
            await asyncio.sleep(5)

    task = asyncio.create_task(background_consolidator())

    yield
    task.cancel()


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handles unhandled exceptions globally for the FastAPI application.

    Logs the exception and returns a standardized error response.

    Args:
        request (Request): The incoming HTTP request that caused the exception.
        exc (Exception): The unhandled exception.

    Returns:
        JSONResponse: A 500 Internal Server Error response with a standardized error message.
    """

    logger.error(f"Unhandled exception in {request.url.path}: {repr(exc)}")
    return JSONResponse(
        status_code=500, content=ErrorResponse(message="Internal server error").dict()
    )


@root_router.get("/favicon.ico", include_in_schema=False)
def favicon():
    # To avoid impacting Prometheus metrics
    raise HTTPException(status_code=404)


app.include_router(root_router)

app.include_router(url.router)
app.include_router(stats.router)
