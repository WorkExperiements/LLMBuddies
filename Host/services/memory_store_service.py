import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

class MemoryStoreService:
    def __init__(self, storage_path: str = "website_memory.json") -> None:
        self.storage_path = storage_path
        if not os.path.exists(self.storage_path):
            self._init_storage()

    def _init_storage(self) -> None:
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump({}, f)

    def _load_memory(self) -> Dict[str, Dict[str, Any]]:
        with open(self.storage_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_memory(self, memory: Dict[str, Dict[str, Any]]) -> None:
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2)

    def store_website_content(self, url: str, raw_text: str, summary: str) -> None:
        memory = self._load_memory()
        memory[url] = {
            "raw_text": raw_text,
            "summary": summary,
            "last_updated": datetime.now().isoformat()
        }
        self._save_memory(memory)

    def get_website_content(self, url: str) -> Optional[Dict[str, str]]:
        memory = self._load_memory()
        return memory.get(url)

    def list_all_urls(self) -> List[str]:
        return list(self._load_memory().keys())

    def clear(self) -> None:
        self._save_memory({})