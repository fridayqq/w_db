import streamlit as st
import psycopg2
import pandas as pd
import os
import requests
import json

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

st.title("Wallet Manager")

st.markdown("""
<style>
.main .block-container { 
    max-width: 1400px; 
    padding: 1rem;
}
.element-container:has(> .stDataFrame) {
    height: calc(100vh - 200px);
}
</style>
""", unsafe_allow_html=True)



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
        cursor.execute("SELECT id, address, name, wallet_type FROM project1.wallets")
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
def add_wallet(address, name, wallet_type):
    try:
        if not check_connection():
            st.error("Соединение с базой данных не установлено. Подключитесь заново.")
            return
        cursor = st.session_state.conn.cursor()
        cursor.execute("INSERT INTO project1.wallets (address, name, wallet_type) VALUES (%s, %s, %s) RETURNING id", (address, name, wallet_type))
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

# Add new functions after existing functions
def clear_all_wallets():
    try:
        if not check_connection():
            st.error("Соединение с базой данных не установлено")
            return False
        cursor = st.session_state.conn.cursor()
        cursor.execute("DELETE FROM project1.wallets")
        st.session_state.conn.commit()
        return True
    except Exception as e:
        st.error(f"Ошибка при очистке базы: {e}")
        return False

def import_from_excel(df, address_col, name_col, type_col):
    try:
        if not check_connection():
            st.error("Соединение с базой данных не установлено")
            return False
        cursor = st.session_state.conn.cursor()
        for _, row in df.iterrows():
            cursor.execute(
                "INSERT INTO project1.wallets (address, name, wallet_type) VALUES (%s, %s, %s)",
                (str(row[address_col]), str(row[name_col]), str(row[type_col]))
            )
        st.session_state.conn.commit()
        return True
    except Exception as e:
        st.error(f"Ошибка при импорте: {e}")
        return False

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

        # Create two columns
        left_col, right_col = st.columns(2)

        # Update the left column section
        with left_col:
            st.subheader("Данные из базы")
            if st.button("Получить данные из БД"):
                wallets = get_wallet_addresses_with_names()
                if wallets:
                    st.session_state.wallets_df = pd.DataFrame(wallets, columns=["ID", "Адрес", "Имя", "wallet_type"])
            
            # Always display data if it exists in session state
            if st.session_state.wallets_df is not None:
                st.dataframe(st.session_state.wallets_df, hide_index=True, use_container_width=True, height=6000)

        # Right column - All other operations
        with right_col:
            # st.subheader("Поиск записей")
            # search_field = st.selectbox("Поле для поиска", ["id", "address", "name"])
            # search_value = st.text_input("Значение для поиска")
            # if st.button("Найти записи"):
            #     search_results = search_wallets(search_field, search_value)
            #     if search_results:
            #         search_df = pd.DataFrame(search_results, columns=["ID", "Адрес", "Имя"])
            #         st.dataframe(
            #             search_df,
            #             use_container_width=True,
            #             height=400
            #         )
            #     else:
            #         st.info("Записей не найдено.")

            st.subheader("Добавление новой записи")
            new_address = st.text_input("Адрес нового кошелька")
            new_name = st.text_input("Имя нового кошелька")
            new_wallet_type = st.text_input("wallet_type кошелька")
            if st.button("Добавить запись"):
                add_wallet(new_address, new_name, new_wallet_type)

            st.subheader("Редактирование записи")
            wallet_id_to_update = st.text_input("ID записи для обновления")
            field_to_update = st.selectbox("Поле для обновления", ["address", "name", "wallet_type"])
            new_value = st.text_input("Новое значение")
            if st.button("Обновить запись"):
                update_wallet(wallet_id_to_update, field_to_update, new_value)

            st.subheader("Удаление записи")
            wallet_id_to_delete = st.text_input("ID записи для удаления")
            if st.button("Удалить запись"):
                delete_wallet(wallet_id_to_delete)

            st.subheader("Управление базой")
            if st.button("Очистить базу кошельков", key="clear_db", type="secondary", icon="🚨"):
                if clear_all_wallets():
                    st.success("База успешно очищена")
                    st.session_state.wallets_df = None

            st.subheader("Импорт из Excel")
            uploaded_file = st.file_uploader("Выберите Excel файл", type=['xlsx', 'xls'])

            if uploaded_file is not None:
                df = pd.read_excel(uploaded_file)
                columns = df.columns.tolist()

                col1, col2, col3 = st.columns(3)
                with col1:
                    address_col = st.selectbox("Столбец с адресами", columns)
                with col2:
                    name_col = st.selectbox("Столбец с именами", columns)
                with col3:
                    type_col = st.selectbox("Столбец с типами", columns)

                if st.button("Импортировать данные"):
                    if import_from_excel(df, address_col, name_col, type_col):
                        st.success("Данные успешно импортированы")
                        wallets = get_wallet_addresses_with_names()
                        if wallets:
                            st.session_state.wallets_df = pd.DataFrame(
                                wallets, 
                                columns=["ID", "Адрес", "Имя", "wallet_type"]
                            )
            st.subheader("Обновление вебхука")
            if st.button("Обновить вебхук", key="update_webhook", type="secondary", icon="🚨"):
                update_webhook()

        
else:
    st.warning("Авторизуйтесь, чтобы получить доступ к функционалу.")
