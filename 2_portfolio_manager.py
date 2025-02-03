import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import plotly.express as px


st.set_page_config(layout="wide")
st.title("Portfolio Manager")

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

def check_connection():
    if "conn" not in st.session_state or st.session_state.conn.closed != 0:
        return False
    return True

def get_wallet_addresses_with_names():
    try:
        if not check_connection():
            st.error("Соединение с базой данных не установлено. Подключитесь заново.")
            return []
        cursor = st.session_state.conn.cursor()
        cursor.execute("SELECT * FROM project1.txs order by id ASC")
        wallets = cursor.fetchall()
        return wallets
    except Exception as e:
        st.error(f"Ошибка при получении кошельков: {e}")
        return []

def get_wallet_stats():
    try:
        if not check_connection():
            st.error("Соединение с базой данных не установлено")
            return None
        cursor = st.session_state.conn.cursor()
        query = """
        SELECT 
            w.address,
            w.name,
            COUNT(DISTINCT t.id) as total_txs,
            COUNT(DISTINCT CASE WHEN t.mint_out = 'So11111111111111111111111111111111111111112' THEN t.id END) as sol_txs,
            COUNT(DISTINCT t.mint_in) as unique_mint_in
        FROM project1.wallets w
        LEFT JOIN project1.txs t ON w.address = t.wallet
        GROUP BY w.address, w.name
        ORDER BY total_txs DESC
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    except Exception as e:
        st.error(f"Ошибка при получении статистики: {e}")
        return None

# Main execution flow
if "conn" not in st.session_state or st.session_state.conn.closed != 0:
    if st.button("Подключиться к базе данных"):
        st.session_state.conn = create_connection(host, port, dbname, user, password)
        if st.session_state.conn:
            st.success("Подключение успешно установлено!")

if check_connection():
    with st.spinner('Подготовка данных...'):
        stats = get_wallet_stats()
        if stats:
            st.session_state.stats_df = pd.DataFrame(
                stats,
                columns=["Адрес", "Имя", "Всего транзакций", "SOL транзакций", "Уникальных mint_in"]
            )
            st.success('Данные успешно загружены')
            
            password = st.text_input("Введите пароль для просмотра графиков", type="password")
            if st.button("Показать графики"):
                if password == "solana228":
                    # Create visualization
                    fig = px.bar(
                        st.session_state.stats_df,
                        x="Имя",
                        y=["Всего транзакций", "SOL транзакций", "Уникальных mint_in"],
                        title="Статистика транзакций по кошелькам",
                        barmode="group"
                    )
                    
                    fig.update_layout(
                        xaxis_title="Кошелёк",
                        yaxis_title="Количество",
                        legend_title="Тип",
                        height=600
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Неверный пароль")
else:
    st.error("Нет подключения к базе данных")