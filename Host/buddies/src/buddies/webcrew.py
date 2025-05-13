from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task, tool
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import ScrapeWebsiteTool
from typing import List

@CrewBase
class WebCrew():
  """Buddies crew for web analysis"""
  agents: List[BaseAgent]
  tasks: List[Task]
  _website_url: str
  tasks_config = 'config/web_tasks.yaml'  # Set as class variable

  def __init__(self, website_url: str):
      """Initialize WebCrew with a website URL
      
      Args:
          website_url: The URL of the website to analyze
      """
      self._website_url = website_url
      self.modelToUse = LLM(
          model="openai/llama-3.1-8b-lexi-uncensored-v2",
          base_url="http://localhost:1234/v1",
          api_key="1234"
      )

  @tool
  def scrape_website_tool(self) -> ScrapeWebsiteTool:
      """Get the tool for scraping websites"""
      #return ScrapeWebsiteTool(website_url=self._website_url)
      return ScrapeWebsiteTool()

  @agent
  def web_extractor(self) -> Agent:
      return Agent(
          config=self.agents_config['web_extractor'], # type: ignore[index]
          verbose=True,
          memory=True,
          llm=self.modelToUse,
          tools=[self.scrape_website_tool()],
          allow_delegation=False  # Since this is a single agent setup
      )
  
  @task
  def analyze_webpage_task(self) -> Task:
      return Task(
          config=self.tasks_config['analyze_webpage_task'] # type: ignore[index]
      )
  
  @crew
  def web_crew(self) -> Crew:
      """Creates a single-agent crew for web analysis"""
      return Crew(
          agents=[self.web_extractor()],
          tasks=[self.analyze_webpage_task()],
          process=Process.sequential,
          verbose=True
      )