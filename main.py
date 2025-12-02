import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))) 
import streamlit as st
import pandas as pd
from backend_logic import AppController, NewsArticle 
from datetime import datetime, timedelta
import time

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
                                st.success(message + " Silakan beralih ke mode Login.")
                                st.session_state.auth_mode = "Login" 
                                st.rerun() 
                            else:
                                st.error(message)


def history_page():
    st.title("History Pencarian Offline")
    st.info("Riwayat ini dimuat dari file 'search_history.json'.")
    
    history_data = st.session_state.controller.history.get_history()
    
    if not history_data:
        st.warning("Belum ada riwayat pencarian yang tersimpan.")
        return

    df = pd.DataFrame(history_data)
    
    if not df.empty:
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
    df = df[['Waktu Pencarian', 'query', 'category']]
    df.columns = ['Waktu Pencarian', 'Kata Kunci', 'Kategori']
    
    st.dataframe(df, use_container_width=True, height=300)
    
    st.markdown("---")
    if st.button("Clear All History", help="Menghapus semua entri di file JSON lokal."):
        st.session_state.controller.history.clear_history()
        st.success("Semua riwayat pencarian berhasil dihapus.")
        st.rerun()

def home_page():
    st.title("GoodNews")
    st.header("Berita Prioritas Terkini")

    with st.sidebar:
        st.subheader("Pencarian Berita")
        search_query_input = st.text_input("Masukkan Kata Kunci:", key="search_query_home")
        
        if st.button("Cari Berita", type='primary', use_container_width=True):
            if search_query_input:
                st.session_state.search_query = search_query_input
                with st.spinner(f"Mencari dan Memprioritaskan '{st.session_state.search_query}'..."):
                    articles = st.session_state.controller.search_and_rank_news(st.session_state.search_query, max_results=15) 
                    st.session_state.current_articles = articles 
                    if not articles:
                        st.error("Tidak ada berita yang ditemukan atau ada masalah dengan API Key GNews.")
            else:
                st.warning("Masukkan kata kunci pencarian.")
    
    if st.session_state.current_articles:
        
        st.subheader("Visualisasi Skor Prioritas Artikel Teratas")
        chart_data = pd.DataFrame([
            {'Judul Singkat': a.title[:30] + '...', 'Score': a.score} 
            for a in st.session_state.current_articles[:10] 
        ])
        chart_data = chart_data.set_index('Judul Singkat') 
        
        st.bar_chart(chart_data)
        st.markdown("---")
        

        st.subheader(f"Hasil Prioritas untuk '{st.session_state.search_query}' ({len(st.session_state.current_articles)} Artikel)")
        
        for article in st.session_state.current_articles:
            try:
                published_str = article.published_at.strftime('%d %b %Y %H:%M')
            except AttributeError:
                published_str = 'Tanggal N/A'
                
            st.markdown(f"**[{article.score}]: [{article.title}]({article.url})**") 
            st.caption(f"Sumber: {article.source_name} | {published_str}")
            st.write(article.description)
            st.markdown("---")
    else:
        st.info("Masukkan kata kunci di sidebar untuk mulai pencarian berita.")


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