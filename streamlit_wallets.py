import streamlit as st
import psycopg2
import pandas as pd
import os

# Получение данных для подключения к базе данных из переменных окружения
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT", "5432")
dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

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

# Функция для получения данных из базы данных
def get_wallets():
    try:
        if not check_connection():
            st.error("Соединение с базой данных не установлено. Подключитесь заново.")
            return None
        query = "SELECT * FROM project1.wallets;"
        df = pd.read_sql(query, st.session_state.conn)
        return df
    except Exception as e:
        st.error(f"Ошибка при получении данных: {e}")
        return None

# Функция для поиска записей
def search_wallets(search_field, search_value):
    try:
        if not check_connection():
            st.error("Соединение с базой данных не установлено. Подключитесь заново.")
            return None
        query = f"SELECT * FROM project1.wallets WHERE {search_field}::text ILIKE %s;"
        df = pd.read_sql(query, st.session_state.conn, params=[f"%{search_value}%"])
        return df
    except Exception as e:
        st.error(f"Ошибка при поиске данных: {e}")
        return None

# Функция для обновления записей
def update_wallet(wallet_id, field, new_value):
    try:
        if not check_connection():
            st.error("Соединение с базой данных не установлено. Подключитесь заново.")
            return
        cursor = st.session_state.conn.cursor()
        query = f"UPDATE project1.wallets SET {field} = %s WHERE id = %s"
        cursor.execute(query, (new_value, wallet_id))
        if cursor.rowcount == 0:
            st.error("Нет такой записи для обновления!")
        else:
            st.session_state.conn.commit()
            st.success("Запись обновлена!")
    except Exception as e:
        st.error(f"Ошибка при обновлении записи: {e}")

# Функция для удаления записи
def delete_wallet(delete_field, delete_value):
    try:
        if not check_connection():
            st.error("Соединение с базой данных не установлено. Подключитесь заново.")
            return
        cursor = st.session_state.conn.cursor()
        query = f"DELETE FROM project1.wallets WHERE {delete_field} = %s"
        cursor.execute(query, (delete_value,))
        if cursor.rowcount == 0:
            st.error("Нет такой записи для удаления!")
        else:
            st.session_state.conn.commit()
            st.success("Запись удалена!")
    except Exception as e:
        st.error(f"Ошибка при удалении записи: {e}")

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

# Streamlit UI
st.title("Кошельки из базы данных PostgreSQL")

# Поля для ввода имени пользователя и пароля
username = st.text_input("Имя пользователя")
password = st.text_input("Пароль", type="password")

# Кнопка авторизации
if st.button("Авторизоваться"):
    if username == "admin" and password == "admin_pass":
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
else:
    st.warning("Авторизуйтесь, чтобы получить доступ к функционалу.")
