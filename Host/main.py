from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import httpx
from typing import Optional, Dict, List
from pydantic import BaseModel
from contextlib import asynccontextmanager
from config import get_available_models, get_system_message

# LMStudio API configuration
LMSTUDIO_BASE_URL = "http://localhost:1234"
LMSTUDIO_CHAT_URL = f"{LMSTUDIO_BASE_URL}/v1/chat/completions"

# Global http client
http_client = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    model_id: str
    history: List[ChatMessage]

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient()
    yield
    if http_client:
        await http_client.aclose()

app = FastAPI(lifespan=lifespan)

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

@app.post("/chat")
async def chat(chat_request: ChatRequest):
    try:
        if not chat_request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
            
        if not chat_request.model_id:
            raise HTTPException(status_code=400, detail="Model ID must be provided")
        
        # Start with system message
        messages = [{"role": "system", "content": get_system_message()}]
        
        # Add conversation history
        messages.extend([{"role": msg.role, "content": msg.content} for msg in chat_request.history])
        
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
                timeout=30.0  # 30 second timeout
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"LMStudio API error: {response.text}"
                )
            
            response_data = response.json()
            assistant_message = response_data['choices'][0]['message']['content']
            
            return {"response": assistant_message}
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="LMStudio request timed out")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Error communicating with LMStudio: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)