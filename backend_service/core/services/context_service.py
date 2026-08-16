"""
Context service to manage temporary state. (Using memory for simplicity, but now persisting to file to preserve limits across restarts)
"""
import json
import os
import threading

class ContextService:
    def __init__(self):
        self.file_path = os.path.join(os.getcwd(), "context_data.json")
        self.lock = threading.Lock()
        self.contexts = self._load_from_disk()
        
    def _load_from_disk(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
        
    def _save_to_disk(self):
        with self.lock:
            try:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.contexts, f, ensure_ascii=False)
            except Exception:
                pass

    def save_context(self, session_id: str, key: str, value: str):
        if session_id not in self.contexts:
            self.contexts[session_id] = {}
        self.contexts[session_id][key] = value
        self._save_to_disk()
        
    def load_context(self, session_id: str) -> dict:
        return self.contexts.get(session_id, {})
        
    def delete_context(self, session_id: str, key: str):
        if session_id in self.contexts and key in self.contexts[session_id]:
            del self.contexts[session_id][key]
            self._save_to_disk()
