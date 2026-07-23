"""
Context service to manage temporary state. (Using memory for simplicity)
"""
class ContextService:
    def __init__(self):
        self.contexts = {}
        
    def save_context(self, session_id: str, key: str, value: str):
        if session_id not in self.contexts:
            self.contexts[session_id] = {}
        self.contexts[session_id][key] = value
        
    def load_context(self, session_id: str) -> dict:
        return self.contexts.get(session_id, {})
        
    def delete_context(self, session_id: str, key: str):
        if session_id in self.contexts and key in self.contexts[session_id]:
            del self.contexts[session_id][key]
