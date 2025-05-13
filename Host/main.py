import logging
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
from config import (
    get_available_models, 
    get_system_message, 
    get_lmstudio_base_url,
    get_app_port
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Also configure uvicorn's root logger to show all levels
logging.getLogger().setLevel(logging.DEBUG)

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
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        
    Returns:
        List of properly formatted message dictionaries
    """
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in messages
    ]

def handle_payload(raw_payload: str) -> ChatRequest:
    """
    Handle the incoming payload and convert it to a ChatRequest object.
    
    Args:
        payload: The raw JSON payload as a string
    """
    # Parse the JSON string manually
    payload_dict = json.loads(raw_payload)
    logger.info("Successfully parsed JSON payload")
    
    # Convert history items to ChatMessage objects
    history = [ChatMessage(**msg) for msg in payload_dict.get('history', [])]
    
    # Construct ChatRequest object manually
    chat_request = ChatRequest(
        message=payload_dict['message'],
        model_id=payload_dict['model_id'],
        history=history,
        session_id=payload_dict.get('session_id'),
        url_enabled=payload_dict.get('url_enabled', False),
        url=payload_dict.get('url')
    )
    return chat_request


async def save_chat_session(
    session_id: str,
    history: List[ChatMessage],
    user_message: str,
    assistant_message: str,
    db: Session
) -> None:
    """
    Save or update a chat session with new messages
    
    Args:
        session_id: The ID of the session to save
        history: Previous chat history
        user_message: The latest user message
        assistant_message: The latest assistant response
        db: Database session
    """
    try:
        logger.info(f"Saving session {session_id}")
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        
        # Convert ChatMessage objects to dictionaries for storage
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
    except Exception as e:
        # Log the error but don't fail the chat request
        logger.error(f"Error saving session: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize services
    global crew_service, lm_studio_service
    crew_service = CrewService()
    lm_studio_service = LMStudioService()
    yield
    # Cleanup
    if crew_service:
        crew_service.cleanup()
    if lm_studio_service:
        await lm_studio_service.close()

app = FastAPI(lifespan=lifespan, debug=True)

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
async def chat(request: Request, db: Session = Depends(get_db)):
    try:
        # Get raw body content as string
        body = await request.body()
        raw_payload = body.decode('utf-8')
        logger.info("Received raw payload: %s", raw_payload)
        
        try:
            chat_request = handle_payload(raw_payload)
        except json.JSONDecodeError as json_err:
            logger.error(f"JSON parsing error: {str(json_err)}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {str(json_err)}")
        except KeyError as key_err:
            logger.error(f"Missing required field: {str(key_err)}")
            raise HTTPException(status_code=400, detail=f"Missing required field: {str(key_err)}")
        except Exception as e:
            logger.error(f"Error processing payload: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=400, detail=f"Error processing payload: {str(e)}")

        if not chat_request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
            
        if not chat_request.model_id:
            raise HTTPException(status_code=400, detail="Model ID must be provided")
        
        logger.info(f"Processing chat request with model {chat_request.model_id}")
        logger.info(f"URL enabled: {chat_request.url_enabled}, URL: {chat_request.url}")
        
        # Create history string for crew service
        history = "\n".join([
            f"{msg.role}: {msg.content}" 
            for msg in chat_request.history
        ])
        
        # Get response from appropriate service based on URL flag
        try:
            if chat_request.url_enabled:
                logger.info(f"Processing URL analysis request for: {chat_request.url}")
                assistant_message = await crew_service.process_chat(
                    message=chat_request.message,
                    history=history,
                    url=chat_request.url
                )
            else:
                # Use LM Studio for chat
                logger.info("Using llm service for chat")
                
                # Prepare messages with system message and history
                messages = transform_to_chat_messages([
                    {"role": "system", "content": get_system_message()},
                    *[{"role": msg.role, "content": msg.content} for msg in chat_request.history],
                    {"role": "user", "content": chat_request.message}
                ])
                
                assistant_message = await lm_studio_service.get_chat_completion(
                    messages=messages,
                    model_id=chat_request.model_id
                )
                
        except Exception as service_error:
            logger.error(f"Service error: {str(service_error)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
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
                logger.error(f"Session save error: {str(session_error)}")
                # Don't fail the request if session save fails
        else:
            logger.info("No session ID provided, not saving session.")
            
        return {"response": assistant_message}
            
    except HTTPException as http_ex:
        # Log HTTP exceptions
        logger.error(f"HTTP Exception: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Convert all other exceptions to a proper JSON response with 500 status
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    
    # Configure uvicorn logging
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Set all loggers to DEBUG level
    for logger in log_config["loggers"]:
        log_config["loggers"][logger]["level"] = "DEBUG"
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=get_app_port(),
        reload=True,
        log_config=log_config,
        log_level="debug"
    )

