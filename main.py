import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))) 
import streamlit as st
import pandas as pd
from backend_logic import AppController, NewsArticle 
from datetime import datetime, timedelta
import time

# --- STATE MANAGEMENT & INITIALIZATION ---
LOGO_PATH = 'logo.jpg' 

if 'controller' not in st.session_state:
    st.session_state.controller = AppController()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'current_page' not in st.session_state:
    st.session_state.current_page = "login"
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = "Login"
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'current_articles' not in st.session_state:
    st.session_state.current_articles = []

@st.cache_data
def convert_df_to_csv(df):
    """Mengubah DataFrame ke format CSV untuk diunduh."""
    return df.to_csv(index=False).encode('utf-8')


def login_register_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>GoodNews</h1>", unsafe_allow_html=True)
        if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, width=200)
        
        st.markdown("<h3 style='text-align: center;'>Login atau Daftar Akun</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.session_state.auth_mode = st.radio(
            "Pilih Mode", ["Login", "Daftar Akun Baru"], 
            horizontal=True, 
            key="auth_mode_radio"
        )

        if st.session_state.auth_mode == "Login":
            with st.form("login_form"):
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("LOGIN", type='primary')
                
                if submitted:
                    with st.spinner("Memproses Login..."):
                        time.sleep(0.5)
                        if st.session_state.controller.auth.login(username, password):
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.current_page = "home"
                            st.success(f"Login Berhasil! Selamat datang, {username}.")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Username atau Password salah.") 
        
        else: 
            with st.form("register_form"):
                
                new_username = st.text_input("Username Baru", key="register_username")
                new_password = st.text_input("Password Baru", type="password", key="register_password")
                confirm_password = st.text_input("Konfirmasi Password", type="password", key="confirm_password")
                
                submitted_register = st.form_submit_button("DAFTAR", type='secondary')

                if submitted_register:
                    if new_password != confirm_password:
                        st.error("Password dan Konfirmasi Password tidak cocok.")
                    else:
                        with st.spinner("Mendaftarkan Akun..."):
                            time.sleep(0.5)
                            success, message = st.session_state.controller.auth.register(new_username, new_password)
                            if success: 
                                st.success(message + " Selamat, Akun anda telah terdaftar! Silakan Login.") 
                                st.session_state.auth_mode = "Login" 
                            else:
                                st.error(message)


def history_page():
    current_username = st.session_state.username
    st.title("History Pencarian Offline")
    st.info(f"Riwayat ini dimuat dari file 'search_history.json' untuk user: **{current_username}**.")
    
    history_data = st.session_state.controller.get_search_history(current_username)
    
    if not history_data:
        st.warning("Belum ada riwayat pencarian yang tersimpan.")
        return

    df = pd.DataFrame(history_data)
    
    if not df.empty:
        # VISUALISASI 2 (Tambahan): Aktivitas Harian & Top Queries
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        daily_searches = df.groupby('date').size().reset_index(name='Jumlah Pencarian')
        daily_searches['date'] = daily_searches['date'].astype(str)
        
        st.subheader("Aktivitas Pencarian Harian")
        st.line_chart(daily_searches.set_index('date')) 
        st.markdown("---")

        top_queries = df['query'].value_counts().head(5).reset_index(name='Frekuensi')
        top_queries.columns = ['Kata Kunci', 'Frekuensi']
        st.subheader("5 Kata Kunci Teratas")
        st.bar_chart(top_queries.set_index('Kata Kunci'))
        st.markdown("---")
        
    df['Waktu Pencarian'] = df['timestamp'].dt.strftime('%d-%m-%Y %H:%M:%S')
    df_display = df[['Waktu Pencarian', 'query', 'category']]
    df_display.columns = ['Waktu Pencarian', 'Kata Kunci', 'Kategori']
    
    # EXPORT LAPORAN RIWAYAT (CSV)
    csv_history = convert_df_to_csv(df_display)
    st.download_button(
        label="Download Riwayat Pencarian (CSV)",
        data=csv_history,
        file_name=f"Riwayat_Pencarian_{current_username}.csv",
        mime="text/csv",
    )
    st.markdown("---")
    
    st.dataframe(df_display, use_container_width=True, height=300)
    
    st.markdown("---")
    if st.button("Clear All History", help="Menghapus semua entri di file JSON lokal."):
        st.session_state.controller.clear_search_history(current_username)
        st.success("Semua riwayat pencarian berhasil dihapus.")
        st.rerun()

# --- Helper function untuk membuat konten Laporan HTML/PDF (untuk semua artikel) ---
def generate_report_content(articles, query):
    """Membuat konten HTML (Offline Report) untuk export semua artikel."""
    html_content = f"""
    <html>
        <head>
            <title>GoodNews Report: {query}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #555; border-bottom: 2px solid #ccc; padding-bottom: 5px; }}
                .article {{ margin-bottom: 30px; padding: 15px; border: 1px solid #eee; border-radius: 5px; }}
                pre {{ white-space: pre-wrap; word-wrap: break-word; background-color: #f9f9f9; padding: 10px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <h1>GoodNews Report: {query}</h1>
            <p>Dibuat oleh: {st.session_state.username} pada: {datetime.now().strftime('%d %B %Y %H:%M:%S')}</p>
            <hr>
    """
    
    for i, article in enumerate(articles[:10]):
        published_str = article.published_at.strftime('%d %b %Y %H:%M') if article.published_at else 'Tanggal N/A'
        
        html_content += f"""
            <div class="article">
                <h2>{i+1}. {article.title}</h2>
                <p><b>Skor Prioritas:</b> {article.score} | <b>Sumber:</b> {article.source_name} | <b>Waktu:</b> {published_str}</p>
                
                <h3>Deskripsi GNews:</h3>
                <p>{article.description}</p>
                
                <h3>Isi Lengkap (Offline Content):</h3>
                <pre>{article.content if article.content else 'Konten tidak tersedia di API.'}</pre>
                
                <p>Link Asli: <a href="{article.url}">{article.url}</a></p>
            </div>
        """
    html_content += "</body></html>"
    return html_content

# --- Helper function BARU untuk membuat laporan HTML satu artikel (dengan summary) ---
def generate_single_report_content(article: NewsArticle, summary: str):
    """Membuat konten HTML untuk satu artikel dengan Ringkasan AI."""
    published_str = article.published_at.strftime('%d %b %Y %H:%M') if article.published_at else 'Tanggal N/A'
    
    html_content = f"""
    <html>
        <head>
            <title>Ringkasan AI: {article.title[:50]}...</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
                h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 5px; }}
                .metadata {{ background-color: #f0f8ff; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
                pre {{ white-space: pre-wrap; word-wrap: break-word; background-color: #f9f9f9; padding: 15px; border-radius: 3px; border: 1px solid #ccc; }}
                .ai-summary {{ color: #28a745; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>{article.title}</h1>
            
            <div class="metadata">
                <p><b>Skor Prioritas:</b> {article.score}</p>
                <p><b>Sumber:</b> {article.source_name}</p>
                <p><b>Tanggal Publikasi:</b> {published_str}</p>
            </div>
            
            <h2>✅ Ringkasan AI</h2>
            <div class="ai-summary">
                <pre>{summary}</pre>
            </div>
            
            <h2>Konten Lengkap (Offline Content)</h2>
            <pre>{article.content if article.content else 'Konten tidak tersedia atau gagal di-scrape.'}</pre>
            
            <p>Link Asli: <a href="{article.url}">{article.url}</a></p>
        </body>
    </html>
    """
    return html_content
# --------------------------------------------------------------------------


def home_page():
    st.title("GoodNews")
    st.header("Berita Prioritas Terkini")

    with st.sidebar:
        st.subheader("Pencarian Berita")
        search_query_input = st.text_input("Masukkan Kata Kunci:", key="search_query_home")
        
        if st.button("Cari Berita", type='primary', use_container_width=True):
            if search_query_input:
                st.session_state.search_query = search_query_input
                with st.spinner(f"Mencari, Memprioritaskan, dan Mengambil Konten '{st.session_state.search_query}'..."):
                    articles = st.session_state.controller.search_and_rank_news(
                        st.session_state.username, 
                        st.session_state.search_query, 
                        max_results=15
                    ) 
                    st.session_state.current_articles = articles 
                    if not articles:
                        st.error("Tidak ada berita yang ditemukan atau ada masalah dengan API Key GNews.")
            else:
                st.warning("Masukkan kata kunci pencarian.")
    
    # --- Logic Memuat Default News (jika tidak ada pencarian sebelumnya) ---
    if not st.session_state.current_articles and st.session_state.controller.current_pq.size() > 0:
        st.session_state.current_articles = st.session_state.controller.current_pq.get_all_articles()
        if not st.session_state.search_query: # Hanya atur query default jika belum ada
            st.session_state.search_query = "Berita Populer (Default)"
    # -----------------------------------------------------------------------

    
    if st.session_state.current_articles:
        
        # VISUALISASI 1: Skor Prioritas (Bar Chart) - Bukti Max Heap
        st.subheader("Visualisasi Skor Prioritas Artikel Teratas")
        chart_data = pd.DataFrame([
            {'Judul Singkat': a.title[:30] + '...', 'Score': a.score} 
            for a in st.session_state.current_articles[:10] 
        ])
        chart_data = chart_data.set_index('Judul Singkat') 
        st.bar_chart(chart_data)
        st.markdown("---")
        
        # EXPORT LAPORAN SEMUA ARTIKEL
        col_csv, col_pdf = st.columns(2)
        
        article_list_for_csv = [{
            'Skor': a.score, 'Judul': a.title, 'Deskripsi': a.description, 'Sumber': a.source_name, 
            'Waktu_Publikasi': a.published_at.strftime('%Y-%m-%d %H:%M:%S') if a.published_at else 'N/A', 
            'URL': a.url, 'Konten_Lengkap': a.content 
        } for a in st.session_state.current_articles]
        
        df_export = pd.DataFrame(article_list_for_csv)
        csv = convert_df_to_csv(df_export)
        
        report_data = generate_report_content(st.session_state.current_articles, st.session_state.search_query)
        
        with col_csv:
            st.download_button(
                label="Download Data Artikel (CSV)",
                data=csv,
                file_name=f"Data_Artikel_{st.session_state.search_query.replace(' ', '_')}.csv",
                mime="text/csv",
                help="Mengunduh data mentah dan konten lengkap (teks) dari semua hasil.",
                use_container_width=True
            )

        with col_pdf:
            # Mengubah label untuk mencerminkan cetak ke PDF
            st.download_button(
                label="Download Laporan PDF (Cetak)",
                data=report_data.encode('utf-8'), 
                file_name=f"Laporan_Offline_{st.session_state.search_query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html",
                help="Mengunduh laporan HTML. Buka di browser lalu gunakan Ctrl+P untuk menyimpannya sebagai PDF.",
                use_container_width=True
            )
        st.markdown("---")
        # ---------------------------------------------

        st.subheader(f"Hasil Prioritas untuk '{st.session_state.search_query}' ({len(st.session_state.current_articles)} Artikel)")
        
        for article in st.session_state.current_articles:
            try: published_str = article.published_at.strftime('%d %b %Y %H:%M')
            except AttributeError: published_str = 'Tanggal N/A'
                
            st.markdown(f"**[{article.score}]: [{article.title}]({article.url})**") 
            st.caption(f"Sumber: {article.source_name} | {published_str}")
            st.write(article.description)
            
            if article.content and article.content.startswith("[Error") == False:
                st.text("Konten (Offline Snippet): " + article.content[:300] + "...")
            
            
            # --- LOGIC & TOMBOL RINGKASAN AI DAN DOWNLOAD SATU ARTIKEL ---
            col_sum, col_down = st.columns([1, 1])
            summary_key = f"summary_{article.url}"
            
            with col_sum:
                # Tombol Ringkas dengan AI
                if st.button("Ringkas dengan AI", key=f"summarize_{article.url}", type='secondary', use_container_width=True):
                    article_to_summarize = st.session_state.controller.get_article_by_url(article.url)
                    if article_to_summarize:
                        with st.spinner("Menganalisis dan Meringkas dengan AI Gemini..."):
                            summary = st.session_state.controller.summarizer.summarize_text(article_to_summarize.content)
                            st.session_state[summary_key] = summary
                        st.rerun() 
            
            # 2. TAMPILKAN RINGKASAN DAN TOMBOL DOWNLOAD TUNGGAL
            if summary_key in st.session_state and st.session_state[summary_key]:
                with st.expander("⬇️ Hasil Ringkasan AI", expanded=True):
                    summary_text = st.session_state[summary_key]
                    st.success(summary_text)

                    # --- TOMBOL DOWNLOAD SATU ARTIKEL (Hanya muncul setelah Ringkasan dibuat) ---
                    report_single = generate_single_report_content(article, summary_text)
                    
                    with col_down:
                        st.download_button(
                            label="Download Laporan Tunggal (HTML/PDF)",
                            data=report_single.encode('utf-8'),
                            file_name=f"Report_AI_{article.title[:20].replace(' ', '_')}.html",
                            mime="text/html",
                            help="Mengunduh artikel ini, Ringkasan AI, dan konten lengkap. Dapat dicetak ke PDF.",
                            use_container_width=True
                        )
                        
            st.markdown("---")
    else:
        st.error("Tidak ada berita yang ditemukan. Pastikan API Key GNews valid dan berfungsi.")


def main_app_layout():
    with st.sidebar:
        if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, width=100)
        st.header(f"Halo, {st.session_state.username}")
        st.markdown("---")
        
        if st.button("Home/Menu", use_container_width=True):
            st.session_state.current_page = "home"
        if st.button("History", use_container_width=True):
            st.session_state.current_page = "history"
        
        st.markdown("---")
        if st.button("Logout", type='secondary', use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.current_page = "login"
            st.rerun()

    if st.session_state.current_page == "home":
        home_page()
    elif st.session_state.current_page == "history":
        history_page()

if st.session_state.logged_in:
    main_app_layout()
else:
    login_register_page()