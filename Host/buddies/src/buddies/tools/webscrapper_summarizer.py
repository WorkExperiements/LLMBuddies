import time
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from crewai_tools import ScrapeWebsiteTool
from crewai import Agent, Crew, Process, Task, LLM
import json
from services.lm_studio import LMStudioService
from config import AGENT_MODEL_ID

class ScrapeAndSummarizeInput(BaseModel):
    url: str = Field(..., description="The full URL of the website to scrape and summarize.")

class ScrapeAndSummarizeTool(BaseTool):
    name: str = "ScrapeAndSummarizeTool"
    description: str = "Scrapes a webpage from a given URL and returns both the raw content and a summary."
    args_schema: Type[BaseModel] = ScrapeAndSummarizeInput

    def _run(self, url: str) -> str:
        # Step 1: Scrape the raw content
        raw_text = ScrapeWebsiteTool().run(website_url=url)
        print("******Raw text length:", len(raw_text))

        # Step 2: Get summary using synchronous LMStudioService
        lm_studio = LMStudioService()
        summary = lm_studio.get_chat_completion(
            messages=[{
                "role": "user", 
                "content": f"Summarize the following website content, do not include any other information like acknowledgements:\n\n{raw_text[:2000]}"
            }],
            model_id=AGENT_MODEL_ID
        )

        result = {
            "raw": raw_text[:2000], 
            "summary": summary
        }

        print(f"***** Tool executed successfully: {summary} ******")

        return json.dumps(result)