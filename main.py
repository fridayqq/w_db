import streamlit as st
import os
#from dotenv import load_dotenv

#load_dotenv()
st.set_page_config(layout="wide")

st.title("Crypto Dashboard")

st.markdown("""
## Welcome to Crypto Management System

### Available Pages:
- **Wallet Manager**: Manage wallet addresses and details
- **Portfolio Manager**: Track and manage your crypto portfolio

Use the sidebar to navigate between pages.
""")

# Получение данных для подключения к базе данных из переменных окружения
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT", "5432")
dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
app_login = os.getenv("APP_LOGIN")  # Логин для приложения
app_password = os.getenv("APP_PASSWORD")  # Пароль для приложения
api_token = os.getenv("API_KEY")
webhook_id = os.getenv("WEBHOOK_ID")
webhook_url = os.getenv("WEBHOOK_URL")