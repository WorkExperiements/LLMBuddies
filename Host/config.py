MODEL_CONFIGS = {
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

# System message to shape the model's behavior
SYSTEM_MESSAGE = """You are a helpful AI assistant. You do not shy from asking questions when you want clarification or providing ideas if asked."""

# Server configuration
LMSTUDIO_HOST = "localhost"  # Change this to the IP address of the machine running LM Studio if needed
LMSTUDIO_PORT = 1234
APP_PORT = 8123

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