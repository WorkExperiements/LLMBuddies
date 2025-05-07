from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

@CrewBase
class Buddies():
    """Buddies crew for general conversation"""

    agents: List[BaseAgent]
    tasks: List[Task]

    modelToUse = LLM(
        model="openai/llama-3.1-8b-lexi-uncensored-v2",
        base_url="http://localhost:1234/v1",
        api_key="1234"
    )
    @agent
    def chatbot(self) -> Agent:
        return Agent(
            name="Chatbot",
            role="A friendly and knowledgeable AI assistant that can engage in general conversation.",
            goal="To engage in helpful conversation with the user.",
            backstory="I am an AI assistant with broad knowledge across many topics. I aim to be helpful while being clear about my capabilities and limitations.",
            verbose=True,
            llm=self.modelToUse,
            allow_delegation=False  # Since this is a single agent setup
        )

    @task
    def chat_task(self) -> Task:
        return Task(
            config=self.tasks_config['chat_task'] # type: ignore[index]
        )
        # return Task(
        #     description="""
        #         Engage in conversation with the user and provide helpful responses to the user input based on existing conversation history from -- {user_input}.
        #     """,
        #     expected_output="""
        #         the Assistant response to the user message based on this conversation history -- {user_input}.
        #     """,
        #     agent=self.chatbot()
        # )

    @crew
    def crew(self) -> Crew:
        """Creates a single-agent crew for chat interactions"""
        return Crew(
            agents=[self.chatbot()],
            tasks=[self.chat_task()],
            process=Process.sequential,
            verbose=True
        )
