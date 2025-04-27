MODEL_CONFIGS = {
    "llama-3.1-8b-lexi-a-v2":"D:\\cc\\GPT4All\\bartowski\\Llama-3.1-8B-Lexi-g-V2-GGUF\\Llama-3.1-8B-Lexi-g-V2-Q6_K_L.gguf",
    "llama-3.2-1b-b_open_v_gguf": "D:\\cc\\GPT4All\\Novaciano\\Llama-3.2-1B-b_Open_v_GGUF\\Llama-3.2-1B-b_Open_v.gguf",
    "mistral-7b-bstory-lora": "D:\\cc\\GPT4All\\hrtdind\\Mistral-7B-bSTORY-lora-GGUF\\Mistral-7B-bSTORY-q5_K_M.gguf"
}

# System message to shape the model's behavior
SYSTEM_MESSAGE = """You are a helpful AI assistant. Please provide clear, concise, and accurate responses.
Be friendly but professional in your interactions."""

def get_model_path(model_id: str) -> str:
    """Get the full path for a model ID"""
    return MODEL_CONFIGS.get(model_id)

def get_available_models() -> dict:
    """Get all available model configurations"""
    return {
        model_id: {"id": model_id, "path": path}
        for model_id, path in MODEL_CONFIGS.items()
    }

def get_system_message() -> str:
    """Get the system message for the chat"""
    return SYSTEM_MESSAGE