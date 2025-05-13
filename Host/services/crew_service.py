from typing import Dict, Optional
import logging
import traceback
from buddies.src.buddies.crew import ChatCrew
from buddies.src.buddies.webcrew import WebCrew

logger = logging.getLogger(__name__)

class CrewService:
    """Service for managing and interacting with different AI crews"""
    
    def __init__(self):
        self._chat_crew = None
        self._web_crew = None
        logger.info("Initialized CrewService")
    
    def _get_chat_crew(self) -> ChatCrew:
        """Get or create the chat crew instance"""
        if not self._chat_crew:
            logger.info("Creating new chat crew instance")
            self._chat_crew = ChatCrew()
        return self._chat_crew

    def _get_web_crew(self, website_url: str) -> WebCrew:
        """Get or create the web crew instance
        
        Args:
            website_url: The URL of the website to analyze
        """
        logger.info(f"Creating new web crew instance for URL: {website_url}")
        # Always create a new instance since the URL might be different
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
            # Log request details
            logger.info(f"Processing chat - URL provided: {'yes' if url else 'no'}")
            logger.info(f"Message: {message}")
            
            if url:
                # Use web crew for URL analysis
                logger.info(f"Processing URL analysis with web crew: {url}")
                crew = self._get_web_crew(website_url=url)
                inputs = {
                    "question": f"{history}\nuser: {message}",
                    "url": url
                }
                logger.info("Calling web crew with inputs")
                try:
                    result = crew.web_crew().kickoff(inputs=inputs)
                except Exception as crew_error:
                    logger.error(f"Web crew error: {str(crew_error)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise Exception(f"Web crew error: {str(crew_error)}")
            else:
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
            raise Exception(f"Service: Error processing chat with crew: {str(e)}")
    
    def cleanup(self):
        """Cleanup any resources if needed"""
        logger.info("Cleaning up CrewService")
        self._chat_crew = None
        self._web_crew = None