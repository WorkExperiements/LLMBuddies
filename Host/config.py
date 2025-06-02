MODEL_CONFIGS = {
    "hermes-3-llama-3.1-8b":{
        "path": "D:/cc/GPT4All/NousResearch/Hermes-3-Llama-3.1-8B-GGUF/Hermes-3-Llama-3.1-8B.Q4_K_M.gguf",
        "display_name": "Hermes 3.1 (8B)"
    },
    "llama-3.1-8b-claude-3.7-sonnet-reasoning-distilled":{
        "path": "D:/cc/GPT4All/reedmayhew/Llama-3.1-8B-claude-3.7-sonnet-reasoning-distilled/llama-3.1-8b-claude-3.7-sonnet-reasoning-distilled.Q4_0.gguf",
        "display_name": "Llama 3.1 8b Claude - distilled"
    },
    "claude-3.7-sonnet-reasoning-gemma3-12b": {
        "path":"D:\\cc\\GPT4All\\reedmayhew\\claude-3.7-sonnet-reasoning-gemma3-12B\\claude-3.7-sonnet-reasoning-gemma3-12B.Q8_0.gguf",
        "display_name": "Claude 3.7 (12B)"
    },
    "llama-3.1-8b-lexi-a-v2": {
        "path": "D:\\cc\\GPT4All\\bartowski\\Llama-3.1-8B-Lexi-g-V2-GGUF\\Llama-3.1-8B-Lexi-g-V2-Q6_K_L.gguf",
        "display_name": "Llama 3.1 (8B) - Lexi"
    },
    "llama-3.2-1b-b_open_v_gguf": {
        "path": "D:\\cc\\GPT4All\\Novaciano\\Llama-3.2-1B-b_Open_v_GGUF\\Llama-3.2-1B-b_Open_v.gguf",
        "display_name": "Llama 3.2 (1B)"
    },
    "mistral-7b-bstory-lora": {
        "path": "D:\\cc\\GPT4All\\hrtdind\\Mistral-7B-bSTORY-lora-GGUF\\Mistral-7B-bSTORY-q5_K_M.gguf",
        "display_name": "Mistral (7B) - Story"
    }
}

# Model ID to use for AI agents (like the web scraper summarizer)
# For now hard code it to gpt, because of some system message issues.
#AGENT_MODEL_ID = "hermes-3-llama-3.1-8b"
AGENT_MODEL_ID = "gpt-3.5-turbo"

# System message to shape the model's behavior
SYSTEM_MESSAGE = """You are a helpful AI assistant. You do not shy from asking questions when you want clarification or providing ideas if asked."""

# Server configuration
LMSTUDIO_HOST = "localhost"  # Change this to the IP address of the machine running LM Studio if needed
LMSTUDIO_PORT = 1234
APP_PORT = 8000

def get_model_path(model_id: str) -> str:
    """Get the full path for a model ID"""
    return MODEL_CONFIGS[model_id]["path"]

def get_available_models() -> dict:
    """Get all available model configurations"""
    return {
        model_id: {
            "id": model_id,
            "display_name": config["display_name"],
            "path": config["path"]
        }
        for model_id, config in MODEL_CONFIGS.items()
    }

def get_system_message() -> str:
    """Get the system message for the chat"""
    return SYSTEM_MESSAGE

def get_lmstudio_base_url() -> str:
    """Get the base URL for LM Studio API"""
    return f"http://{LMSTUDIO_HOST}:{LMSTUDIO_PORT}"

def get_app_port() -> int:
    """Get the port for the web application"""
    return APP_PORT

def get_agent_base_url() ->str:
    """Get the base URL for the agent API"""
    return f"http://{LMSTUDIO_HOST}:{LMSTUDIO_PORT}/v1"