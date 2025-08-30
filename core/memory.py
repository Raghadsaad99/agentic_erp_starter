from collections import deque
from typing import Dict, List

class MemoryStore:
    def __init__(self, k: int = 5):
        self.buffers: Dict[str, deque] = {}
        self.last_domain: Dict[str, str] = {}

    def add_message(self, conv_id: str, sender: str, content: str):
        buf = self.buffers.setdefault(conv_id, deque(maxlen=2*k))
        buf.append({"sender": sender, "content": content})

    def get_window(self, conv_id: str) -> List[dict]:
        return list(self.buffers.get(conv_id, []))

    def set_last_domain(self, conv_id: str, domain: str):
        self.last_domain[conv_id] = domain

    def get_last_domain(self, conv_id: str) -> str:
        return self.last_domain.get(conv_id)
