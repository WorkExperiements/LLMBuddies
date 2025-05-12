from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import ScrapeWebsiteTool
from typing import List

@CrewBase
class WebCrew():
  """Buddies crew for web analysis"""
  agents: List[BaseAgent]
  tasks: List[Task]

  modelToUse = LLM(
      model="openai/llama-3.1-8b-lexi-a-v2",
      base_url="http://localhost:1234/v1",
      api_key="1234"
  )

  scraper = ScrapeWebsiteTool()

  @agent
  def webAnalyzer(self) -> Agent:
      return Agent(
          config=self.agent_config['web_extractor'], # type: ignore[index]
          verbose=True,
          memory=True,
          llm=self.modelToUse,
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
          agents=[self.webAnalyzer()],
          tasks=[self.analyze_webpage_task()],
          process=Process.sequential,
          verbose=True
      )