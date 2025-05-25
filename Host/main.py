import os
import litellm
from config import AGENT_MODEL_ID, get_agent_base_url
# Having a hard time specifying the model on a per agent basis, so we set it globally
os.environ['OPENAI_API_KEY'] = "999"  # or "lm-studio" or any dummy key
os.environ['LITELLM_MODEL']=f"{AGENT_MODEL_ID}" # openai/gpt-3.5-turbo
os.environ['LITELLM_API_BASE']=get_agent_base_url()#"http://localhost:1234/v1"
litellm.model_cost = {
    f"{AGENT_MODEL_ID}": {
        "input_cost_per_token": 0.0,
        "output_cost_per_token": 0.0
    }
}
#litellm._turn_on_debug()

import warnings
# Filter out specific warning types
warnings.filterwarnings("ignore", 
    message=".*is not a Python type.*", 
    category=UserWarning,
    module="pydantic._internal._generate_schema"
)
warnings.filterwarnings("ignore", 
    message=".*websockets.legacy is deprecated.*", 
    category=DeprecationWarning,
    module="websockets.legacy"
)
warnings.filterwarnings("ignore", 
    message=".*WebSocketServerProtocol is deprecated.*", 
    category=DeprecationWarning,
    module="uvicorn.protocols.websockets.websockets_impl"
)

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, List
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from database import get_db, ChatSession
from services.crew_service import CrewService
from services.lm_studio import LMStudioService
from services.models.chat_message import ChatMessage
import json
import traceback 
import sys
from config import (
    get_available_models, 
    get_system_message, 
    get_lmstudio_base_url,
    get_app_port
)

# Global services
crew_service = None
lm_studio_service = None

class ChatRequest(BaseModel):
    message: str
    model_id: str
    history: List[ChatMessage] = []
    session_id: Optional[str] = None
    url_enabled: bool = False
    url: Optional[str] = None

def transform_to_chat_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Transform a list of message dictionaries into the format expected by LM Studio.
    This method ensures consistent message formatting.
    """
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in messages
    ]

def handle_payload(raw_payload: str) -> ChatRequest:
    """Handle the incoming payload and convert it to a ChatRequest object"""
    payload_dict = json.loads(raw_payload)
    history = [ChatMessage(**msg) for msg in payload_dict.get('history', [])]
    
    return ChatRequest(
        message=payload_dict['message'],
        model_id=payload_dict['model_id'],
        history=history,
        session_id=payload_dict.get('session_id'),
        url_enabled=payload_dict.get('url_enabled', False),
        url=payload_dict.get('url')
    )

async def save_chat_session(
    session_id: str,
    history: List[ChatMessage],
    user_message: str,
    assistant_message: str,
    db: Session
) -> None:
    """Save or update a chat session with new messages"""
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        
        history_dicts = [msg.dict() for msg in history]
        new_messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message}
        ]
        
        if not session:
            session = ChatSession(
                id=session_id,
                history=history_dicts + new_messages
            )
            db.add(session)
        else:
            session.history = history_dicts + new_messages
        db.commit()
    except Exception:
        pass  # Silently handle any session saving errors

@asynccontextmanager
async def lifespan(app: FastAPI):
    global crew_service, lm_studio_service
    crew_service = CrewService()
    lm_studio_service = LMStudioService()
    yield
    if crew_service:
        crew_service.cleanup()
    if lm_studio_service:
        lm_studio_service.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/models/configured")
async def list_configured_models():
    return get_available_models()

@app.get("/chat/session/{session_id}")
async def get_chat_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        return {"history": []}
    return {"history": session.history}

@app.post("/chat")
async def chat(request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.body()
        raw_payload = body.decode('utf-8')
        
        try:
            chat_request = handle_payload(raw_payload)
        except json.JSONDecodeError:
            print("JSON Parsing Error:", file=sys.stderr)
            traceback.print_exc()
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        except Exception as e:
            print(f"Payload Processing Error: {str(e)}", file=sys.stderr)
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=str(e))

        if not chat_request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
            
        if not chat_request.model_id:
            raise HTTPException(status_code=400, detail="Model ID must be provided")

        # Create history string for crew service
        history = "\n".join([
            f"{msg.role}: {msg.content}" 
            for msg in chat_request.history
        ])
        
        # Get response from appropriate service based on URL flag
        try:
            if chat_request.url_enabled:
                assistant_message = crew_service.process_chat(
                    message=chat_request.message,
                    history=history,
                    url=chat_request.url
                )
            else:
                messages = transform_to_chat_messages([
                    {"role": "system", "content": get_system_message()},
                    *[{"role": msg.role, "content": msg.content} for msg in chat_request.history],
                    {"role": "user", "content": chat_request.message}
                ])
                
                # Use synchronous get_chat_completion
                assistant_message = lm_studio_service.get_chat_completion(
                    messages=messages,
                    model_id=chat_request.model_id
                )
        except Exception as service_error:
            print("Service Error:", file=sys.stderr)
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Error processing chat: {str(service_error)}"
            )
        
        # Save session if a session_id is provided
        if chat_request.session_id and chat_request.session_id.strip():
            try:
                await save_chat_session(
                    session_id=chat_request.session_id,
                    history=chat_request.history,
                    user_message=chat_request.message,
                    assistant_message=assistant_message,
                    db=db
                )
            except Exception as session_error:
                # Print session errors but don't fail the request
                print(f"Session Save Error: {str(session_error)}", file=sys.stderr)
                traceback.print_exc()
            
        return {"response": assistant_message}
            
    except HTTPException:
        raise
    except Exception as e:
        print("Unexpected Error:", file=sys.stderr)
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=get_app_port(),
        reload=True,
        log_level="info",  # Changed from "error" to "info" to show startup messages
        access_log=None    # Keep this to avoid request logging spam
    )

