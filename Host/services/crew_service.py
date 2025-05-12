from typing import Dict, Optional
import logging
import traceback
from buddies.src.buddies.crew import Buddies
# Temporarily commenting out web crew import
# from buddies.src.buddies.webcrew import WebCrew

logger = logging.getLogger(__name__)

class CrewService:
    """Service for managing and interacting with different AI crews"""
    
    def __init__(self):
        self._chat_crew = None
        # Temporarily disabled
        # self._web_crew = None
        logger.info("Initialized CrewService")
    
    def _get_chat_crew(self) -> Buddies:
        """Get or create the chat crew instance"""
        if not self._chat_crew:
            logger.info("Creating new chat crew instance")
            self._chat_crew = Buddies()
        return self._chat_crew
    
    # Temporarily disabled
    # def _get_web_crew(self) -> WebCrew:
    #     """Get or create the web crew instance"""
    #     if not self._web_crew:
    #         logger.info("Creating new web crew instance")
    #         self._web_crew = WebCrew()
    #     return self._web_crew

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
            url: Optional URL to analyze (temporarily disabled)
            
        Returns:
            The assistant's response as a string
        """
        try:
            # Temporarily disabled URL handling
            if url:
                logger.info("URL functionality is temporarily disabled")
                return "URL analysis is temporarily disabled. Please try regular chat instead."
            
            # Use chat crew for regular conversations
            logger.info("Processing regular chat message")
            crew = self._get_chat_crew()
            inputs = {
                "user_input": f"{history}\nuser: {message}"
            }
            logger.info("Calling chat crew with inputs")
            try:
                result = crew.crew().kickoff(inputs=inputs)
            except Exception as crew_error:
                logger.error(f"Chat crew error: {str(crew_error)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise Exception(f"Chat crew error: {str(crew_error)}")
            
            return result.raw
            
        except Exception as e:
            print("Service: Error processing chat")
            logger.error(f"Service: Inside Service Error processing chat: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Service:Error processing chat with crew: {str(e)}")

    def cleanup(self):
        """Cleanup any resources if needed"""
        logger.info("Cleaning up CrewService")
        self._chat_crew = None
        # Temporarily disabled
        # self._web_crew = None