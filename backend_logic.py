import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any


class NewsArticle: 
    pass

class NewsPriorityQueue: 
    pass

class Trie:
    pass

class GNewsAPIClient:
    pass

class GeminiSummarizer:
    pass


class AuthService:
    """Layanan otentikasi sederhana dengan penyimpanan pengguna di file JSON."""
    def __init__(self, users_file="users.json"):
        self.users_file = users_file
        self.users = self._load_users()
        
        if not self.users:
            self.users = {"user1": "pass1", "admin": "admin123", "praktikum": "strukturdata"}
            self._save_users()

    def _load_users(self):
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_users(self):
        with open(self.users_file, "w") as f:
            json.dump(self.users, f, indent=4)

    def login(self, username, password):
        return self.users.get(username) == password

    def register(self, username, password):
        if not username or not password:
            return False, "Username dan password tidak boleh kosong."
        if username in self.users:
            return False, "Username sudah terdaftar. Silakan pilih username lain."
        
        self.users[username] = password
        self._save_users()
        return True, "Pendaftaran berhasil! Silakan login."


class SearchHistory:
    """Mengelola riwayat pencarian (disimpan ke file JSON lokal)."""
    def __init__(self, history_file="search_history.json"):
        self.history_file = history_file
        self.history: List[Dict[str, Any]] = self._load_history()
        
        if not self.history:
            self.history.append({"query": "Contoh: Kebijakan Energi", "category": "Politik", "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()})
            self.history.append({"query": "Contoh: AI di Indonesia", "category": "Teknologi", "timestamp": (datetime.now() - timedelta(days=1)).isoformat()})
            self._save_history() 

    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    return json.load(f)
            except Exception:
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


class AppController:
    """Kelas Kontroler Minimal untuk Demo Minggu 1."""
    def __init__(self):
        self.auth = AuthService()
        self.history = SearchHistory()
        
        self.gnews_client = None 
        self.summarizer = None
        self.trie = None
        self.current_pq = None

    def get_search_history(self):
        return self.history.get_history()
