import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
from ml_models.ml_model import train_model
import numpy as np
import hashlib

# ----------------- Auth Helpers ------------------ #

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user_table():
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, password TEXT)')
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('INSERT INTO users(username, password) VALUES (?, ?)', (username, hash_password(password)))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hash_password(password)))
    data = c.fetchone()
    conn.close()
    return data

# ----------------- App Core ------------------ #

def fetch_data():
    try:
        conn = sqlite3.connect('data/database.db')
        query = "SELECT * FROM cryptocurrency_data"
        df = pd.read_sql(query, conn)
        conn.close()

        df['last_updated'] = pd.to_datetime(df['last_updated'])
        df.set_index('last_updated', inplace=True)

        return df
    except Exception as e:
        st.error(f"Failed to fetch data from database: {e}")
        return None

def show_basic_info(df):
    st.title("Cryptocurrency Dashboard")

    unique_coins_df = df.drop_duplicates(subset=['symbol'])

    for _, row in unique_coins_df.iterrows():
        with st.container():
            col1, col2 = st.columns([1, 2])

            with col1:
                st.image(row['image'], width=64)
                st.header(f"{row['name']} ({row['symbol'].upper()})")
                st.subheader(f"Price: ${row['current_price']:.2f}")
                st.markdown(f"Market Cap: ${row['market_cap']:,}")
                st.markdown(f"24H Change: {row['price_change_percentage_24h']:.2f}%")
                st.subheader("Market Stats")
                st.markdown(f"Volume (24H): ${row['total_volume']:,}")
                st.markdown(f"High (24H): ${row['high_24h']:.2f}")
                st.markdown(f"Low (24H): ${row['low_24h']:.2f}")

                model, latest_time = train_model(df, row['symbol'])
                if model:
                    future_time = [[latest_time + 3600]]
                    predicted_price = model.predict(future_time)[0]
                    st.markdown(f"Predicted Price (1h later): ${predicted_price:.2f}")

            with col2:
                st.subheader("Historical Price Chart")
                fig, ax = plt.subplots(figsize=(6, 4))
                coin_df = df[df['symbol'] == row['symbol']]
                ax.plot(coin_df.index, coin_df['current_price'], label="Price", color="green")
                ax.axhline(row['high_24h'], color="red", linestyle="--", label="High (24H)")
                ax.axhline(row['low_24h'], color="blue", linestyle="--", label="Low (24H)")
                ax.axhline(row['current_price'], color="yellow", linestyle="--", label="Current Price")
                max_price = max(coin_df['current_price'].max(), row['high_24h'])
                ax.set_ylim(0, max_price * 1.1)
                ax.set_xlabel("Time")
                ax.set_ylabel("Price (USD)")
                ax.set_title(f"Price Trend: {row['name']}")
                ax.legend()
                st.pyplot(fig)

        st.markdown("---")

def cumulative_graph(df):
    st.title("Cumulative Cryptocurrency Price Chart")

    cumulative_df = df.groupby(['last_updated', 'name'])['current_price'].mean().unstack()

    fig, ax = plt.subplots(figsize=(10, 6))
    for coin in cumulative_df.columns:
        ax.plot(cumulative_df.index, cumulative_df[coin], label=coin)

    ax.set_title("Cumulative Cryptocurrency Price Trends")
    ax.set_xlabel("Time")
    ax.set_ylabel("Price (USD)")
    ax.legend(title="Cryptocurrencies")
    st.pyplot(fig)

def login_register():
    create_user_table()
    st.sidebar.subheader("User Login / Registration")
    option = st.sidebar.radio("Action", ["Login", "Register"])

    if option == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"Welcome {username}!")
            else:
                st.error("Incorrect username or password")

    elif option == "Register":
        new_user = st.sidebar.text_input("New Username")
        new_pass = st.sidebar.text_input("New Password", type="password")
        if st.sidebar.button("Register"):
            try:
                add_user(new_user, new_pass)
                st.success("Registration successful! You can now login.")
            except sqlite3.IntegrityError:
                st.error("Username already exists.")

    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        st.sidebar.success(f"Logged in as {st.session_state['username']}")
        if st.sidebar.button("Logout"):
            st.session_state.clear()
            st.experimental_rerun()

def main():
    login_register()

    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        df = fetch_data()
        if df is not None and not df.empty:
            show_basic_info(df)
            cumulative_graph(df)
        else:
            st.error("No data available.")
    else:
        st.warning("Please log in to view the dashboard.")

if __name__ == "__main__":
    main()