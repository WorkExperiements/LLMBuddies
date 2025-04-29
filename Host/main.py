from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import Optional, Dict, List
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from database import get_db, ChatSession
import json
from config import (
    get_available_models, 
    get_system_message, 
    get_lmstudio_base_url,
    get_app_port
)

# LMStudio API configuration
LMSTUDIO_BASE_URL = get_lmstudio_base_url()
LMSTUDIO_CHAT_URL = f"{LMSTUDIO_BASE_URL}/v1/chat/completions"

# Global http client
http_client = None

class ChatMessage(BaseModel):
    role: str
    content: str

    def dict(self, *args, **kwargs):
        return {"role": self.role, "content": self.content}

class ChatRequest(BaseModel):
    message: str
    model_id: str
    history: List[ChatMessage]
    session_id: Optional[str] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient()
    yield
    if http_client:
        await http_client.aclose()

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/models/configured")
async def list_configured_models():
    """List all models from our configuration"""
    return get_available_models()

@app.get("/chat/session/{session_id}")
async def get_chat_session(session_id: str, db: Session = Depends(get_db)):
    """Get chat history for a session"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        return {"history": []}
    return {"history": session.history}

@app.post("/chat")
async def chat(chat_request: ChatRequest, db: Session = Depends(get_db)):
    try:
        if not chat_request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
            
        if not chat_request.model_id:
            raise HTTPException(status_code=400, detail="Model ID must be provided")
        
        # Start with system message
        messages = [{"role": "system", "content": get_system_message()}]
        
        # Add conversation history
        messages.extend([msg.dict() for msg in chat_request.history])
        
        # Add new message
        messages.append({"role": "user", "content": chat_request.message})
        
        # Prepare the request for LMStudio API
        payload = {
            "messages": messages,
            "temperature": 0.7,
            "stream": False,
            "model": chat_request.model_id
        }
        
        # Make request to LMStudio
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LMSTUDIO_CHAT_URL,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"LMStudio API error: {response.text}"
                )
            
            response_data = response.json()
            assistant_message = response_data['choices'][0]['message']['content']

            # Only save session if a session_id is provided
            if chat_request.session_id and chat_request.session_id.strip():
                try:
                    print(f"Saving session {chat_request.session_id}")
                    session = db.query(ChatSession).filter(ChatSession.id == chat_request.session_id).first()
                    
                    # Convert ChatMessage objects to dictionaries for storage
                    history_dicts = [msg.dict() for msg in chat_request.history]
                    new_messages = [
                        {"role": "user", "content": chat_request.message},
                        {"role": "assistant", "content": assistant_message}
                    ]
                    
                    if not session:
                        session = ChatSession(
                            id=chat_request.session_id,
                            history=history_dicts + new_messages
                        )
                        db.add(session)
                    else:
                        session.history = history_dicts + new_messages
                    db.commit()
                except Exception as e:
                    # Log the error but don't fail the chat request
                    print(f"Error saving session: {str(e)}")
            else:
                print("No session ID provided, not saving session.")
            
            return {"response": assistant_message}
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="LMStudio request timed out")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Error communicating with LMStudio: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="192.168.0.247", 
        port=get_app_port(), 
        reload=True
    )