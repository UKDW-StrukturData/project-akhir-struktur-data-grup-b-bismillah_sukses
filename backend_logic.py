import json
import os
from datetime import datetime
from typing import List, Dict, Any


class NewsArticle:
   
    def __init__(self, score=0):
        self.score = score

class NewsPriorityQueue:
    def __init__(self):
        pass

class AuthService:
    """Layanan otentikasi sederhana."""
    def __init__(self):
        self.users = {"user1": "pass1", "admin": "admin123", "praktikum": "strukturdata"}

    def login(self, username, password):
        return self.users.get(username) == password


class SearchHistory:
    """Mengelola riwayat pencarian (disimpan ke file JSON lokal)."""
    def __init__(self, history_file="search_history.json"):
        self.history_file = history_file
        self.history: List[Dict[str, Any]] = self._load_history()
      
        if not self.history:
            self.history.append({"query": "Contoh: Kebijakan Energi", "category": "Politik", "timestamp": datetime.now().isoformat()})
            self.history.append({"query": "Contoh: AI di Indonesia", "category": "Teknologi", "timestamp": (datetime.now() - timedelta(days=1)).isoformat()})
            self._save_history() 

    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save_history(self):
        with open(self.history_file, "w") as f:
            json.dump(self.history, f, indent=4)

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history

    def clear_history(self):
        self.history = []
        self._save_history()
