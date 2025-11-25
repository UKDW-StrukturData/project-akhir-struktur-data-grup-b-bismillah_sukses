import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any


class AuthService:
    """Layanan otentikasi sederhana dengan penyimpanan pengguna di file JSON."""
    def __init__(self, users_file="users.json"):
        self.users_file = users_file
        self.users = self._load_users()
        
        if not self.users:
            self.users = {"user1": "pass1", "admin": "admin123", "praktikum": "strukturdata"}
            self._save_users()

    def _load_users(self):
        """Memuat data pengguna dari file JSON."""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {} 
        return {}

    def _save_users(self):
        """Menyimpan data pengguna ke file JSON."""
        with open(self.users_file, "w") as f:
            json.dump(self.users, f, indent=4)

    def login(self, username, password):
        """Mengecek kredensial login."""
        return self.users.get(username) == password

    def register(self, username, password):
        """Mendaftarkan pengguna baru."""
        if not username or not password:
            return False, "Username dan password tidak boleh kosong."
        if username in self.users:
            return False, "Username sudah terdaftar. Silakan pilih username lain."
        
        self.users[username] = password
        self._save_users()
        return True, "Pendaftaran berhasil! Silakan login."

