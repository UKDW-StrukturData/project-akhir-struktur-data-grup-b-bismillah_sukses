import streamlit as st
import pandas as pd
from backend_logic import AuthService, SearchHistory 
from datetime import datetime, timedelta
import time
import os


LOGO_PATH = 'logo.jpg' 

if 'auth_service' not in st.session_state:
    st.session_state.auth_service = AuthService()
if 'history_service' not in st.session_state:
    st.session_state.history_service = SearchHistory()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'current_page' not in st.session_state:
    st.session_state.current_page = "login"
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = "Login"


def login_register_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>GoodNews</h1>", unsafe_allow_html=True)
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=200)
        
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
                        if st.session_state.auth_service.login(username, password):
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
                            success, message = st.session_state.auth_service.register(new_username, new_password)
                            if success:
                                st.success(message + " Silakan beralih ke mode Login.")
                                st.session_state.auth_mode = "Login" 
                                st.rerun() 
                            else:
                                st.error(message)


def history_page():
    st.title("💾 History Pencarian Offline")
    st.info("Riwayat ini dimuat dari file 'search_history.json'.")
    
    history_data = st.session_state.history_service.get_history()
    
    if not history_data:
        st.warning("Belum ada riwayat pencarian yang tersimpan.")
        return

    df = pd.DataFrame(history_data)
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%d-%m-%Y %H:%M:%S')
    df = df[['timestamp', 'query', 'category']]
    df.columns = ['Waktu Pencarian', 'Kata Kunci', 'Kategori']
    
    st.dataframe(df, use_container_width=True, height=300)
    
    st.markdown("---")
    if st.button("Clear All History", help="Menghapus semua entri di file JSON lokal."):
        st.session_state.history_service.clear_history()
        st.success("Semua riwayat pencarian berhasil dihapus.")
        st.rerun()

def home_page():
    st.title("GoodNews (Prioritize: News Ranker)")
    st.header("Home/Menu - Trending Topik")
    st.markdown("---")
    st.info("Fitur inti **Priority Queue** dan **Integrasi API** akan dikerjakan di sini pada Minggu 2 dan 3.")
    st.warning("Saat ini, halaman ini hanya menampilkan placeholder.")


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