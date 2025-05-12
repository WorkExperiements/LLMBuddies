from typing import Dict
from pydantic import BaseModel

class ChatMessage(BaseModel):
    """
    Represents a chat message in the conversation.
    Used for both user and assistant messages.
    """
    role: str
    content: str

    def dict(self, *args, **kwargs) -> Dict[str, str]:
        """Convert the message to a dictionary format expected by LM Studio"""
        return {
            "role": self.role,
            "content": self.content
        }