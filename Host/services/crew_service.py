from typing import Dict, Optional
import traceback
from buddies.src.buddies.crew import ChatCrew
from buddies.src.buddies.webcrew import WebCrew
from services.memory_store_service import MemoryStoreService
import json

class CrewService:
    """Service for managing and interacting with different AI crews"""
    
    def __init__(self):
        self._chat_crew = None
        self._web_crew = None
        self.memory_service = MemoryStoreService()

    def _get_chat_crew(self) -> ChatCrew:
        """Get or create the chat crew instance"""
        if not self._chat_crew:
            self._chat_crew = ChatCrew()
        return self._chat_crew

    def _get_web_crew(self, website_url: str) -> WebCrew:
        """Get or create the web crew instance
        
        Args:
            website_url: The URL of the website to analyze
        """
        self._web_crew = WebCrew(website_url=website_url)
        return self._web_crew

    async def process_chat(
        self,
        message: str,
        history: str,
        url: Optional[str] = None
    ) -> str:
        """
        Process a chat message using the appropriate crew
        
        Args:
            message: The user's message
            history: The conversation history formatted as string
            url: Optional URL to analyze
            
        Returns:
            The assistant's response as a string
        """
        try:
            if url:
                out_message =self._learn_website(url, message)
            else:
                crew = self._get_chat_crew()
                inputs = {
                    "user_input": f"{history}\nuser: {message}"
                }
                try:
                    result = crew.crew().kickoff(inputs=inputs)
                    out_message = result.raw
                except Exception as crew_error:
                    raise Exception(f"Chat crew error: {str(crew_error)}")
            return out_message
            
        except Exception as e:
            raise Exception(f"Service: Error processing chat with crew: {str(e)}")
    
    def _learn_website(self, url: str, message: str) -> str:
        # Check if we've already stored this site
        print(f"Learning website: {url}")
        existing = self.memory_service.get_website_content(url)
        
        if existing:
            print("Content exists for url.")
            return f"I’ve already stored content from {url}. You can ask me about it."
        else:
            print("Content does not exist for url.")

        # Scrape and summarize

        crew = self._get_web_crew(website_url=url)
        inputs = {
            "question": f"user: {message}",
            "url": url
        }
        print(f"Inputs for web crew: {inputs}")
        try:
            result = crew.web_crew().kickoff(inputs=inputs)
        except Exception as crew_error:
            raise Exception(f"Web crew error: {str(crew_error)}")
        print("Crew result:", result.raw)
        print("Crew result length:", len(result.raw))
        result_parsed =json.loads(result.raw)

        self.memory_service.store_website_content(url, result_parsed["raw"], result_parsed["summary"])
        return f"I’ve scraped and stored content from {url}. You can ask me about it later."


    def cleanup(self):
        """Cleanup any resources if needed"""
        self._chat_crew = None
        self._web_crew = None