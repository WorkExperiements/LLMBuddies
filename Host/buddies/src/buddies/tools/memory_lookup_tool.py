from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from services.memory_store_service import MemoryStoreService

class MemoryLookupInput(BaseModel):
    url: str = Field(..., description="The URL of the site to retrieve memory for")

class MemoryLookupTool(BaseTool):
    name: str = "MemoryLookupTool"
    description: str = "Fetches stored memory for a previously scraped website"
    args_schema: Type[BaseModel] = MemoryLookupInput

    def _run(self, url: str) -> str:
        print("Inside the memory lookup tool")
        memory = MemoryStoreService().get_website_content(url)
        if memory:
            return f"Summary:\n{memory['summary']}\n\nRaw:\n{memory['raw'][:3000]}"
        else:
            return f"No memory found for {url}. You may need to learn this site first."