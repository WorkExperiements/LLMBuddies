from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task, tool
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import ScrapeWebsiteTool
from typing import List
from buddies.src.buddies.tools.webscrapper_summarizer import ScrapeAndSummarizeTool
from config import AGENT_MODEL_ID

@CrewBase
class WebCrew():
    """Crew for analyzing and storing content from a website"""
    agents: List[BaseAgent]
    tasks: List[Task]
    _website_url: str
    tasks_config = 'config/web_tasks.yaml'  # This is where your YAML task config lives

    def __init__(self, website_url: str):
        self._website_url = website_url
        self.modelToUse = LLM(
            model=f"{AGENT_MODEL_ID}",
            base_url="http://localhost:1234/v1",
            api_key="1234"
        )

    @agent
    def web_extractor(self) -> Agent:
        return Agent(
            config=self.agents_config['web_extractor'],  # loaded from agents.yaml
            verbose=True,
            memory=True,
            llm=self.modelToUse,
            tools=[ScrapeAndSummarizeTool()],  # ✅ This is a callable function now
            allow_delegation=False
        )

    @task
    def analyze_webpage_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_webpage_task']
        )

    @crew
    def web_crew(self) -> Crew:
        return Crew(
            agents=[self.web_extractor()],
            tasks=[self.analyze_webpage_task()],
            process=Process.sequential,
            verbose=True
        )