import streamlit as st
import pandas as pd
from backend_logic import AuthService, SearchHistory
from datetime import datetime
import time

if 'auth_service' not in st.session_state:
    st.session_state.auth_service = AuthService()
if 'history_service' not in st.session_state:
    st.session_state.history_service = SearchHistory()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""


def login_form():
    st.title("PRIORITIZE: NEWS RANKER")
    st.image('logo.jpg')
    st.subheader("Login Pengguna")
    st.markdown("---")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("LOGIN")
        
        if submitted:
            with st.spinner("Memproses Login..."):
                time.sleep(1) 
                if st.session_state.auth_service.login(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(f"Login Berhasil! Selamat datang, {username}.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Username atau Password salah. Coba: user1/pass1")

def history_page():
    st.title("💾 History Pencarian Offline")
    st.info("Riwayat ini dimuat dari file 'search_history.json' (simulasi data offline).")
    
    history_data = st.session_state.history_service.get_history()
    
    if not history_data:
        st.warning("Belum ada riwayat pencarian yang tersimpan.")
        return

    df = pd.DataFrame(history_data)
    df = df[['timestamp', 'query']]
    df.columns = ['Waktu Pencarian', 'Kata Kunci']
    
    st.dataframe(df, use_container_width=True, height=300)
    
    st.markdown("---")
    if st.button("Clear All History"):
        st.session_state.history_service.clear_history()
        st.success("Semua riwayat pencarian berhasil dihapus.")
        st.rerun()

def main_app():
    
    with st.sidebar:
        st.header(f"Halo, {st.session_state.username}")
        page_selection = st.radio("Navigasi", ["Home/Menu", "History"])
        
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    if page_selection == "History":
        history_page()
    else:
        st.title("PRIORITIZE: NEWS RANKER (Menu Utama)")
        st.header("Home/Menu - Trending Topics")
        st.markdown("---")
        st.info("Halaman ini adalah placeholder. Fitur inti akan dikerjakan di Minggu 2 dan 3.")


if st.session_state.logged_in:
    main_app()
else:
    login_form()
