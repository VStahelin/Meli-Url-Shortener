import logging
import subprocess

from contextlib import asynccontextmanager
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.generator.routes import url, stats
from app.generator.schema import ErrorResponse
from fastapi import HTTPException, FastAPI, APIRouter

from prometheus_fastapi_instrumentator import Instrumentator

logger = logging.getLogger(__name__)

LOCK_KEY = "lock:consolidator"
LOCK_EXPIRE = 10


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Handles the lifespan of the FastAPI application.
    Applies Alembic migrations before starting.
    """
    subprocess.run(["alembic", "upgrade", "head"])
    yield


app = FastAPI(lifespan=lifespan)

root_router = APIRouter()
instrumentator = Instrumentator().instrument(app).expose(app)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception in {request.url.path}: {repr(exc)}")
    return JSONResponse(
        status_code=500, content=ErrorResponse(message="Internal server error").dict()
    )


@root_router.get("/favicon.ico", include_in_schema=False)
def favicon():
    raise HTTPException(status_code=404)


app.include_router(root_router)
app.include_router(url.router)
app.include_router(stats.router)
