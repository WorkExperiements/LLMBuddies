from typing import Dict, Optional
import traceback
from buddies.src.buddies.crew import ChatCrew
from buddies.src.buddies.webcrew import WebCrew

class CrewService:
    """Service for managing and interacting with different AI crews"""
    
    def __init__(self):
        self._chat_crew = None
        self._web_crew = None
    
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
            else:
                crew = self._get_chat_crew()
                inputs = {
                    "user_input": f"{history}\nuser: {message}"
                }
                try:
                    result = crew.crew().kickoff(inputs=inputs)
                except Exception as crew_error:
                    raise Exception(f"Chat crew error: {str(crew_error)}")
            
            return result.raw
            
        except Exception as e:
            raise Exception(f"Service: Error processing chat with crew: {str(e)}")
    
    def cleanup(self):
        """Cleanup any resources if needed"""
        self._chat_crew = None
        self._web_crew = None