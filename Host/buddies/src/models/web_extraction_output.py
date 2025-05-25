from pydantic import BaseModel

class WebExtractionOutput(BaseModel):
    raw: str
    summary: str