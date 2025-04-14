from fastapi import APIRouter

from app.generator.schema import GeneratorRequest

router = APIRouter(prefix="/generate-url", tags=["GenerateURL"])

@router.post("/")
def generate_url(data: GeneratorRequest):
    received_url = data.url
    return {"received_url": received_url}
