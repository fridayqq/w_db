import streamlit as st
import psycopg2
import pandas as pd
import os

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
ADMIN_LOGIN = os.getenv("ADMIN_LOGIN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
USER_LOGIN = os.getenv("USER_LOGIN")
USER_PASSWORD = os.getenv("USER_PASSWORD")

# Функция для получения данных из базы данных
def get_wallets():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        query = "SELECT * FROM project1.wallets;"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Ошибка при подключении к базе данных: {e}")
        return None

# Функция для поиска записей
def search_wallets(search_field, search_value):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        query = f"SELECT * FROM project1.wallets WHERE {search_field}::text ILIKE %s;"
        df = pd.read_sql(query, conn, params=[f"%{search_value}%"])
        conn.close()
        return df
    except Exception as e:
        st.error(f"Ошибка при поиске данных: {e}")
        return None

# Функция для обновления записей в базе данных
def update_wallet(wallet_id, field, new_value):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        query = f"UPDATE project1.wallets SET {field} = %s WHERE id = %s"
        cursor.execute(query, (new_value, wallet_id))
        if cursor.rowcount == 0:
            st.error("Нет такой записи для обновления!")
        else:
            conn.commit()
            st.success("Запись обновлена!")
        conn.close()
    except Exception as e:
        st.error(f"Ошибка при обновлении записи: {e}")

# Функция для удаления записи
def delete_wallet(delete_field, delete_value):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        query = f"DELETE FROM project1.wallets WHERE {delete_field} = %s"
        cursor.execute(query, (delete_value,))
        if cursor.rowcount == 0:
            st.error("Нет такой записи для удаления!")
        else:
            conn.commit()
            st.success("Запись удалена!")
        conn.close()
    except Exception as e:
        st.error(f"Ошибка при удалении записи: {e}")

# Функция для добавления новой записи
def add_wallet(address, name):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute("INSERT INTO project1.wallets (address, name) VALUES (%s, %s) RETURNING id", (address, name))
        new_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        st.success(f"Новая запись добавлена с ID: {new_id}")
    except Exception as e:
        st.error(f"Ошибка при добавлении записи: {e}")

# Функция для проверки логина
def authenticate_user(username, password):
    users = {
        ADMIN_LOGIN: ADMIN_PASSWORD,
        USER_LOGIN: USER_PASSWORD,
    }
    return users.get(username) == password

# Streamlit UI
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Авторизация")
    username = st.text_input("Имя пользователя")
    password = st.text_input("Пароль", type="password")
    if st.button("Войти"):
        if authenticate_user(username, password):
            st.session_state.authenticated = True
            st.experimental_rerun()  # Обновить интерфейс после входа
        else:
            st.error("Неверное имя пользователя или пароль")
else:
    st.title("Кошельки из базы данных PostgreSQL")

    if "wallets_df" not in st.session_state:
        st.session_state.wallets_df = None

    if st.button("Получить данные из БД"):
        st.session_state.wallets_df = get_wallets()

    if st.session_state.wallets_df is not None:
        st.dataframe(st.session_state.wallets_df)

    st.subheader("Поиск записей")
    search_field = st.selectbox("Поле для поиска", ["id", "address", "name"])
    search_value = st.text_input("Значение для поиска")
    if st.button("Найти записи"):
        search_results = search_wallets(search_field, search_value)
        if search_results is not None:
            st.dataframe(search_results)

    st.subheader("Редактирование записи")
    wallet_id = st.number_input("ID записи", min_value=1, step=1)
    field_to_update = st.selectbox("Поле для обновления", ["address", "name"])
    new_value = st.text_input("Новое значение")
    if st.button("Обновить запись"):
        update_wallet(wallet_id, field_to_update, new_value)

    st.subheader("Удаление записи")
    delete_field = st.selectbox("Поле для удаления", ["id", "address", "name"])
    delete_value = st.text_input("Значение для удаления")
    if st.button("Удалить запись"):
        delete_wallet(delete_field, delete_value)

    st.subheader("Добавление новой записи")
    new_address = st.text_input("Адрес кошелька")
    new_name = st.text_input("Имя кошелька")
    if st.button("Добавить запись"):
        add_wallet(new_address, new_name)
