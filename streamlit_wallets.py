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
app_login = os.getenv("APP_LOGIN")  # Логин для приложения
app_password = os.getenv("APP_PASSWORD")  # Пароль для приложения
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
        cursor.execute("SELECT id, address, name FROM project1.wallets")
        wallets = cursor.fetchall()
        return wallets
    except Exception as e:
        st.error(f"Ошибка при получении кошельков: {e}")
        return []

# Функция для поиска записей
def search_wallets(search_field, search_value):
    try:
        if not check_connection():
            st.error("Соединение с базой данных не установлено. Подключитесь заново.")
            return []
        cursor = st.session_state.conn.cursor()
        query = f"SELECT id, address, name FROM project1.wallets WHERE {search_field}::text ILIKE %s"
        cursor.execute(query, (f"%{search_value}%",))
        results = cursor.fetchall()
        return results
    except Exception as e:
        st.error(f"Ошибка при поиске записей: {e}")
        return []

# Функция для обновления вебхука
def update_webhook():
    wallets = [wallet[1] for wallet in get_wallet_addresses_with_names()]
    if len(wallets) == 0:
        st.error("В базе данных нет кошельков. Добавьте адреса в таблицу project1.wallets.")
        return

    payload = {
        "webhookURL": webhook_url,
        "transactionTypes": ["SWAP"],
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

# Функция для добавления новой записи
def add_wallet(address, name):
    try:
        if not check_connection():
            st.error("Соединение с базой данных не установлено. Подключитесь заново.")
            return
        cursor = st.session_state.conn.cursor()
        cursor.execute("INSERT INTO project1.wallets (address, name) VALUES (%s, %s) RETURNING id", (address, name))
        new_id = cursor.fetchone()[0]
        st.session_state.conn.commit()
        st.success(f"Новая запись добавлена с ID: {new_id}")
    except Exception as e:
        st.error(f"Ошибка при добавлении записи: {e}")

# Функция для редактирования записи
def update_wallet(wallet_id, field, new_value):
    try:
        if not check_connection():
            st.error("Соединение с базой данных не установлено. Подключитесь заново.")
            return
        cursor = st.session_state.conn.cursor()
        cursor.execute(f"UPDATE project1.wallets SET {field} = %s WHERE id = %s", (new_value, wallet_id))
        if cursor.rowcount == 0:
            st.error("Нет такой записи для обновления!")
        else:
            st.session_state.conn.commit()
            st.success("Запись успешно обновлена!")
    except Exception as e:
        st.error(f"Ошибка при обновлении записи: {e}")

# Функция для удаления записи
def delete_wallet(wallet_id):
    try:
        if not check_connection():
            st.error("Соединение с базой данных не установлено. Подключитесь заново.")
            return
        cursor = st.session_state.conn.cursor()
        cursor.execute("DELETE FROM project1.wallets WHERE id = %s", (wallet_id,))
        if cursor.rowcount == 0:
            st.error("Нет такой записи для удаления!")
        else:
            st.session_state.conn.commit()
            st.success("Запись успешно удалена!")
    except Exception as e:
        st.error(f"Ошибка при удалении записи: {e}")

# Streamlit UI
st.title("Кошельки из базы данных PostgreSQL")

# Поля для ввода имени пользователя и пароля
username = st.text_input("Имя пользователя")
app_password_input = st.text_input("Пароль", type="password")

# Кнопка авторизации
if st.button("Авторизоваться"):
    if username == app_login and app_password_input == app_password:
        st.session_state.authenticated = True
        st.success("Вы успешно авторизовались!")
    else:
        st.session_state.authenticated = False
        st.error("Неверное имя пользователя или пароль.")

# Проверка авторизации
if "authenticated" in st.session_state and st.session_state.authenticated:
    if "conn" not in st.session_state or st.session_state.conn.closed != 0:
        if st.button("Подключиться к базе данных"):
            st.session_state.conn = create_connection(host, port, dbname, user, password)  # Using DB credentials
            if st.session_state.conn:
                st.success("Подключение успешно установлено!")

    if check_connection():
        if "wallets_df" not in st.session_state:
            st.session_state.wallets_df = None

        if st.button("Получить данные из БД"):
            wallets = get_wallet_addresses_with_names()
            if wallets:
                st.session_state.wallets_df = pd.DataFrame(wallets, columns=["ID", "Адрес", "Имя"])

        if st.session_state.wallets_df is not None:
            st.dataframe(st.session_state.wallets_df)

        st.subheader("Поиск записей")
        search_field = st.selectbox("Поле для поиска", ["id", "address", "name"])
        search_value = st.text_input("Значение для поиска")
        if st.button("Найти записи"):
            search_results = search_wallets(search_field, search_value)
            if search_results:
                search_df = pd.DataFrame(search_results, columns=["ID", "Адрес", "Имя"])
                st.dataframe(search_df)
            else:
                st.info("Записей не найдено.")

        st.subheader("Добавление новой записи")
        new_address = st.text_input("Адрес нового кошелька")
        new_name = st.text_input("Имя нового кошелька")
        if st.button("Добавить запись"):
            add_wallet(new_address, new_name)

        st.subheader("Редактирование записи")
        wallet_id_to_update = st.number_input("ID записи для обновления", min_value=1, step=1)
        field_to_update = st.selectbox("Поле для обновления", ["address", "name"])
        new_value = st.text_input("Новое значение")
        if st.button("Обновить запись"):
            update_wallet(wallet_id_to_update, field_to_update, new_value)

        st.subheader("Удаление записи")
        wallet_id_to_delete = st.number_input("ID записи для удаления", min_value=1, step=1)
        if st.button("Удалить запись"):
            delete_wallet(wallet_id_to_delete)

        st.markdown("""
        <style>
        .streamlit-button-primary { background-color: #4CAF50; color: white; font-weight: bold; border-radius: 5px; }
        </style>
        """, unsafe_allow_html=True)

        st.subheader("Обновление вебхука")
        if st.button("Обновить вебхук", key="update_webhook"):
            update_webhook()
else:
    st.warning("Авторизуйтесь, чтобы получить доступ к функционалу.")
