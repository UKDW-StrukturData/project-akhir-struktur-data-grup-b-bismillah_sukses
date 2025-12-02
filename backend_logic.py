import requests 
import json
import os
import heapq 
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup 
# --- IMPORT GEMINI ---
try:
    from google import genai
    from google.genai.errors import APIError 
except ImportError:
    # Handle jika library belum diinstal
    genai = None
    APIError = type('APIError', (Exception,), {})

# --- KONFIGURASI API ---
# PENTING: Ganti "YOUR_GNEWS_API_KEY_HERE" dengan kunci yang valid!
GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY", "9fa5c1d656b1606ccde69f242f2c1b26") 
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 


class GeminiSummarizer:
    """Class untuk merangkum konten menggunakan Gemini API."""
    def __init__(self):
        self.client = None
        self.model = 'gemini-2.5-flash'
        if genai and GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                print(f"Peringatan: Gagal menginisialisasi klien Gemini: {e}")
                self.client = None

    def summarize_text(self, text_content: str) -> str:
        """Melakukan ringkasan pada teks artikel."""
        if not self.client:
            return "ERROR: Gemini API Key tidak ditemukan atau Summarizer tidak aktif. Silakan setel GEMINI_API_KEY."
        
        if not text_content or text_content.startswith("[Error"):
            return "Gagal membuat ringkasan: Konten artikel tidak tersedia atau gagal di-scrape."
            
        safe_text = text_content[:15000] 
        
        prompt = (
            "Ringkaslah teks berita berikut dalam bahasa Indonesia yang ringkas (maksimal 3 paragraf). "
            "Fokus pada poin-poin utama dan dampaknya. Pastikan outputnya mudah dibaca:\n\n"
            f"TEKS ARTIKEL: {safe_text}"
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except APIError as e:
            return f"ERROR API Gemini: Terjadi kesalahan saat memproses permintaan. ({e})"
        except Exception as e:
            return f"ERROR: Terjadi kesalahan saat meringkas. ({e})"


# ====================================================================
#                          STRUKTUR DATA (MAX HEAP)
# ====================================================================

class NewsArticle:
    """Representasi artikel berita untuk Priority Queue."""
    def __init__(self, title, description, url, published_at, source_name, content, image_url="", score=0):
        self.title = title
        self.description = description
        self.url = url
        self.published_at = published_at
        self.source_name = source_name
        self.content = content 
        self.image_url = image_url
        self.score = score

    def __lt__(self, other):
        """Max Heap: Skor lebih tinggi dianggap 'lebih kecil' (prioritas lebih tinggi)."""
        return self.score > other.score

    def to_dict(self):
        return {
            "title": self.title, "description": self.description, "url": self.url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "source_name": self.source_name, "score": self.score, "content": self.content
        }

class NewsPriorityQueue:
    """Priority Queue (Max Heap) untuk artikel berita."""
    def __init__(self):
        self._heap = [] 

    def push(self, article: NewsArticle):
        heapq.heappush(self._heap, article)

    def size(self) -> int:
        return len(self._heap)

    def get_all_articles(self) -> List[NewsArticle]:
        """Mengembalikan semua artikel dalam urutan prioritas tanpa mengubah heap."""
        temp_list = [heapq.heappop(self._heap) for _ in range(len(self._heap))]
        all_articles = temp_list.copy()
        for article in temp_list:
            heapq.heappush(self._heap, article)
        return all_articles


# ====================================================================
#                        SERVICE & LOGIC
# ====================================================================

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
                with open(self.users_file, "r") as f: return json.load(f)
            except (json.JSONDecodeError, IOError): return {}
        return {}
    def _save_users(self):
        with open(self.users_file, "w") as f: json.dump(self.users, f, indent=4)
    def login(self, username, password): return self.users.get(username) == password
    def register(self, username, password):
        if not username or not password: return False, "Username dan password tidak boleh kosong."
        if username in self.users: return False, "Username sudah terdaftar. Silakan pilih username lain."
        self.users[username] = password; self._save_users(); return True, "Pendaftaran berhasil! Silakan login."


class SearchHistory:
    """Mengelola riwayat pencarian multi-user."""
    def __init__(self, history_file="search_history.json"):
        self.history_file = history_file
        self.history: Dict[str, List[Dict[str, Any]]] = self._load_history()
    
    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
            except Exception:
                return {}
        return {}
        
    def _save_history(self):
        with open(self.history_file, "w") as f: json.dump(self.history, f, indent=4)
        
    def add_to_history(self, username: str, query: str, category: str = None):
        if not username: return
        if username not in self.history:
            self.history[username] = []
            
        user_history = self.history[username]
        entry = {"username": username, "query": query, "category": category, "timestamp": datetime.now().isoformat()}
        
        if not any(e["query"].lower() == query.lower() for e in user_history):
            user_history.insert(0, entry) 
            self._save_history()
            
    def get_history(self, username: str) -> List[Dict[str, Any]]: 
        return self.history.get(username, [])
        
    def clear_history(self, username: str): 
        if username in self.history:
            self.history[username] = []
            self._save_history()


class GNewsAPIClient:
    """Klien untuk koneksi, scraping, dan pemrosesan data dari GNews.io."""
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://gnews.io/api/v4/search"

    def _scrape_article_content(self, url: str) -> str:
        """Mengambil teks isi artikel dari URL sumber (untuk report offline)."""
        try:
            # Menggunakan header umum untuk menghindari pemblokiran
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            paragraphs = soup.find_all('p')
            
            content = '\n'.join([p.get_text() for p in paragraphs if len(p.get_text()) > 50])
            
            return content[:5000] if content else "[Konten tidak ditemukan atau terlalu pendek.]"

        except requests.exceptions.RequestException as e:
            return f"[Error: Gagal mengambil konten dari URL ini. ({e})]"
        except Exception as e:
            return f"[Error: Gagal memproses konten. ({e})]"

    def _calculate_score(self, article_data: Dict[str, Any], query: str) -> int:
        score = 0
        published_at_str = article_data.get("publishedAt")
        if published_at_str:
            try:
                published_datetime = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                time_diff = datetime.now(published_datetime.tzinfo) - published_datetime
                score += max(0, 1000 - int(time_diff.total_seconds() / 3600)) 
            except ValueError:
                pass
        title = article_data.get("title", "").lower()
        description = article_data.get("description", "").lower()
        query_lower = query.lower()
        if query_lower in title: score += 200 
        if query_lower in description: score += 50
        return score

    def get_and_prioritize_news(self, query: str, lang="id", country="id", max_results=15) -> NewsPriorityQueue:
        params = {
            "q": query, "lang": lang, "country": country, "max": max_results, "apikey": self.api_key
        }
        pq = NewsPriorityQueue()
        
        if not self.api_key or self.api_key == "YOUR_GNEWS_API_KEY_HERE":
            return pq 
        
        try:
            response = requests.get(self.base_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            articles_data = data.get("articles", [])
        except requests.exceptions.RequestException:
            return pq 
        
        for art_data in articles_data:
            score = self._calculate_score(art_data, query)
            published_at_dt = None
            if art_data.get("publishedAt"):
                try: published_at_dt = datetime.fromisoformat(art_data["publishedAt"].replace('Z', '+00:00'))
                except ValueError: pass

            article_url = art_data.get("url", "#")
            full_content = self._scrape_article_content(article_url)
            
            article = NewsArticle(
                title=art_data.get("title", "No Title"), description=art_data.get("description", "No Description"),
                url=article_url, published_at=published_at_dt,
                source_name=art_data.get("source", {}).get("name", "Unknown Source"),
                content=full_content, image_url=art_data.get("image", ""), score=score
            )
            pq.push(article)
        return pq


# --- APP CONTROLLER (Final dengan Default Load Logic) ---
class AppController:
    """Mengelola semua layanan backend untuk Streamlit."""
    def __init__(self):
        self.auth = AuthService()
        self.history = SearchHistory()
        self.gnews_client = GNewsAPIClient(GNEWS_API_KEY) 
        self.summarizer = GeminiSummarizer()
        self.current_pq = NewsPriorityQueue() 
        
        self.load_default_news()

    def load_default_news(self, query="Berita Indonesia"):
        """Memuat berita default (populer) jika belum ada hasil."""
        if self.current_pq.size() == 0:
            print(f"Memuat berita default untuk '{query}'...")
            self.current_pq = self.gnews_client.get_and_prioritize_news(query, max_results=10)
        
    def get_search_history(self, username: str):
        return self.history.get_history(username)

    def clear_search_history(self, username: str):
        self.history.clear_history(username)

    def search_and_rank_news(self, username: str, query: str, max_results=15) -> List[NewsArticle]:
        if not query: return []
        
        self.current_pq = self.gnews_client.get_and_prioritize_news(query, max_results=max_results)
        
        if self.current_pq.size() > 0:
            self.history.add_to_history(username, query, category="Umum") 
        
        return self.current_pq.get_all_articles()

    def get_article_by_url(self, target_url: str) -> Optional[NewsArticle]:
        if self.current_pq:
            for article in self.current_pq.get_all_articles():
                if article.url == target_url:
                    return article
        return None