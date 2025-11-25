import streamlit as st
import pandas as pd
from backend_logic import AuthService, SearchHistory
from datetime import datetime, timedelta
import time
import os


def login_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>GoodNews</h1>", unsafe_allow_html=True)
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=200)
        else:
            st.subheader("Logo placeholder")
        
        st.markdown("<h3 style='text-align: center;'>Login atau Daftar Akun</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        auth_mode = st.radio("Pilih Mode", ["Login", "Daftar Akun Baru"], horizontal=True, key="auth_mode_radio")

        if auth_mode == "Login":
            with st.form("login_form"):
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("LOGIN", type='primary')
                
                if submitted:
                    with st.spinner("Memproses Login..."):
                        time.sleep(1)
                        if st.session_state.auth_service.login(username, password):
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.current_page = "home"
                            st.success(f"Login Berhasil! Selamat datang, {username}.")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Username atau Password salah. Coba: user1/pass1")
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
                            time.sleep(1)
                            success, message = st.session_state.auth_service.register(new_username, new_password)
                            if success:
                                st.success(message)
                                st.info("Silakan beralih ke mode Login untuk masuk.")
                                st.session_state.auth_mode_radio = "Login" 
                                st.session_state.current_page = "login"
                                st.rerun() 
                            else:
                                st.error(message)

if st.session_state.logged_in:
    main_app_layout()
else:
    login_page()