from typing import List, Optional, Dict
import httpx
import logging
import traceback
from config import get_lmstudio_base_url, get_system_message
from services.models.chat_message import ChatMessage

logger = logging.getLogger(__name__)

class LMStudioService:
    """Service for interacting with LM Studio's local API"""
    
    def __init__(self):
        self.base_url = get_lmstudio_base_url()
        self.chat_url = f"{self.base_url}/v1/chat/completions"
        self.client = httpx.AsyncClient()
        logger.info(f"Initialized LMStudioService with base URL: {self.base_url}")

    async def close(self):
        """Close the HTTP client"""
        if self.client:
            await self.client.aclose()

    async def get_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model_id: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
    ) -> str:
        """
        Get a chat completion from LM Studio
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model_id: ID of the model to use
            temperature: Temperature for response generation (default: 0.7)
            max_tokens: Maximum tokens to generate (optional)
            top_p: Nucleus sampling parameter (default: 1.0)
            frequency_penalty: Reduces repetition of token sequences (default: 0.0)
            presence_penalty: Reduces repetition of topics (default: 0.0)
            
        Returns:
            The assistant's response as a string
            
        Raises:
            Exception: If the LM Studio API returns an error
        """
        try:
            # Prepare the request payload
            payload = {
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty,
                "stream": False,
                "model": model_id
            }
            
            # Add optional max_tokens if provided
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            
            logger.info(f"Making request to LM Studio with model: {model_id}")
            logger.debug(f"Payload: {payload}")
            
            try:
                # Make request to LM Studio
                response = await self.client.post(
                    self.chat_url,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    error_msg = f"LM Studio API error: {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                response_data = response.json()
                return response_data['choices'][0]['message']['content']
                
            except httpx.TimeoutException as timeout_error:
                logger.error("Request to LM Studio timed out")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise Exception("Request to LM Studio timed out") from timeout_error
            except httpx.HTTPError as http_error:
                logger.error(f"HTTP error occurred: {str(http_error)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise Exception(f"HTTP error occurred: {str(http_error)}") from http_error
                
        except Exception as e:
            logger.error(f"Error in get_chat_completion: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Error getting chat completion: {str(e)}") from e