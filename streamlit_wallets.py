import streamlit as st
import psycopg2
import pandas as pd
import os
import requests
import json

# Получение данных для подключения к базе данных из переменных окружения
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT", "5432")
dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
app_login = os.getenv("USER_LOGIN")
app_password = os.getenv("USER_PASSWORD")
api_token = os.getenv("API_KEY")
webhook_id = os.getenv("WEBHOOK_ID")
webhook_url = os.getenv("WEBHOOK_URL")

# Функция для подключения к базе данных
def create_connection(host, port, dbname, user, password):
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        return conn
    except Exception as e:
        st.error(f"Ошибка при подключении к базе данных: {e}")
        return None

# Функция для проверки подключения
def check_connection():
    if "conn" not in st.session_state or st.session_state.conn.closed != 0:
        return False
    return True

# Функция для получения списка кошельков из базы данных
def get_wallet_addresses_with_names():
    try:
        if not check_connection():
            st.error("Соединение с базой данных не установлено. Подключитесь заново.")
            return []
        cursor = st.session_state.conn.cursor()
        cursor.execute("SELECT address, name FROM project1.wallets")
        wallets = cursor.fetchall()
        return wallets
    except Exception as e:
        st.error(f"Ошибка при получении кошельков: {e}")
        return []

# Функция для обновления вебхука
def update_webhook():
    wallets = [wallet[0] for wallet in get_wallet_addresses_with_names()]
    if len(wallets) == 0:
        st.error("В базе данных нет кошельков. Добавьте адреса в таблицу project1.wallets.")
        return

    payload = {
        "webhookURL": webhook_url,
        "transactionTypes": ["Any"],
        "accountAddresses": wallets,
        "webhookType": "enhanced",
        "txnStatus": "all"
    }

    try:
        response = requests.put(
            f"https://api.helius.xyz/v0/webhooks/{webhook_id}?api-key={api_token}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )

        if response.status_code == 200:
            st.success("Webhook успешно обновлен")
        else:
            st.error(f"Ошибка при обновлении вебхука: {response.status_code}")
    except Exception as e:
        st.error(f"Произошла ошибка: {str(e)}")

# Streamlit UI
st.title("Кошельки из базы данных PostgreSQL")

# Поля для ввода имени пользователя и пароля
username = st.text_input("Имя пользователя")
pwd = st.text_input("Пароль", type="password")

# Кнопка авторизации
if st.button("Авторизоваться"):
    if username == app_login and password == app_password:
        st.session_state.authenticated = True
        st.success("Вы успешно авторизовались!")
    else:
        st.session_state.authenticated = False
        st.error("Неверное имя пользователя или пароль.")

# Проверка авторизации
if "authenticated" in st.session_state and st.session_state.authenticated:
    if "conn" not in st.session_state or st.session_state.conn.closed != 0:
        if st.button("Подключиться к базе данных"):
            st.session_state.conn = create_connection(host, port, dbname, user, password)
            if st.session_state.conn:
                st.success("Подключение успешно установлено!")

    if check_connection():
        if "wallets_df" not in st.session_state:
            st.session_state.wallets_df = None

        if st.button("Получить данные из БД"):
            wallets = get_wallet_addresses_with_names()
            if wallets:
                st.session_state.wallets_df = pd.DataFrame(wallets, columns=["address", "name"])

        if st.session_state.wallets_df is not None:
            st.dataframe(st.session_state.wallets_df)

        st.subheader("Обновление вебхука")
        if st.button("Обновить вебхук", key="update_webhook", use_container_width=True):
            update_webhook()
else:
    st.warning("Авторизуйтесь, чтобы получить доступ к функционалу.")
