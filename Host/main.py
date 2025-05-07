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
from buddies.src.buddies.crew import Buddies
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
        
        # Create a context message that includes the conversation history
        context = "\n".join([
            f"{msg.role}: {msg.content}" 
            for msg in chat_request.history
        ])
        context += f"\nuser: {chat_request.message}"
        
        # Create a chat task and get response from CrewAI
        inputs = {
            "user_input": context,
        }
        chat_crew = Buddies().crew().kickoff(inputs=inputs)
        assistant_message = chat_crew.raw
        print(f"Assistant message: {assistant_message}")
        
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
            
    except Exception as e:
        raise e

if __name__ == "__main__":
# # Testing the crew
    # inputs = {
    #     'topic': 'AI LLMs',
    #     'current_year': str(2023)
    # }
    
    # try:
    #     Buddies().crew().kickoff(inputs=inputs)
    # except Exception as e:
    #     raise Exception(f"An error occurred while running the crew: {e}")
    
    # the web server
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=get_app_port(), 
        reload=True
    )

