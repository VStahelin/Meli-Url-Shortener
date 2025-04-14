from pydantic import BaseModel


class GeneratorRequest(BaseModel):
    url: str
