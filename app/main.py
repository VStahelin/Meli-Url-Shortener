import subprocess
from fastapi import FastAPI, APIRouter
from app.generator.routes import router as generator_router

app = FastAPI()


@app.on_event("startup")
def run_migrations():
    subprocess.run(["alembic", "upgrade", "head"])


root_router = APIRouter()


@root_router.get("/")
def root():
    return {"message": "Welcome to the root endpoint"}


@root_router.get("/{url_id}")
def get_url(url_id: str):
    return {"url_id": url_id}


# Inclui o router da raiz no app
app.include_router(root_router)
app.include_router(generator_router)
