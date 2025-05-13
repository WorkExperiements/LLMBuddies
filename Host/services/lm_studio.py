from typing import List, Optional, Dict
import httpx
from config import get_lmstudio_base_url, get_system_message

class LMStudioService:
    """Service for interacting with LM Studio's local API"""
    
    def __init__(self):
        self.base_url = get_lmstudio_base_url()
        self.chat_url = f"{self.base_url}/v1/chat/completions"
        self.client = httpx.AsyncClient()

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
            httpx.TimeoutException: If the request times out
            httpx.HTTPError: If there's an HTTP-related error
            Exception: For other errors including API errors
        """
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

        # Make request to LM Studio
        response = await self.client.post(
            self.chat_url,
            json=payload,
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise Exception(f"LM Studio API error: {response.text}")
        
        response_data = response.json()
        return response_data['choices'][0]['message']['content']