import streamlit as st
import mysql.connector
from datetime import datetime
import hashlib
import pandas as pd
import matplotlib.pyplot as plt

conn = mysql.connector.connect( # database connection
    host="localhost",
    user="root",
    password="1234",
    database="query_system"
)
cursor = conn.cursor()

def hash_password(password): # PASSWORD HASH
    return hashlib.sha256(password.encode()).hexdigest()

def signup(username, email, password, role): # data stored in database
    hashed_pw = hash_password(password)
    cursor.execute(
        "INSERT INTO users (username, email, password, role) VALUES (%s,%s,%s,%s)",
        (username, email, hashed_pw, role)
    )
    conn.commit()

def login(email, password): # check the user
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    if user:
        if user[3] == hash_password(password):
            return user
    return None

def create_query(email, title, desc): # query detail added in database
    now = datetime.now()
    cursor.execute(
        """INSERT INTO queries 
        (client_email, title, description, status, raised_at) 
        VALUES (%s,%s,%s,%s,%s)""",
        (email, title, desc, "Open", now)
    )
    conn.commit()

def get_client_queries(email): 
    cursor.execute("SELECT * FROM queries WHERE client_email=%s", (email,))
    return cursor.fetchall()

def get_all_queries():
    cursor.execute("SELECT * FROM queries")
    return cursor.fetchall()

def close_query(qid):
    now = datetime.now()
    cursor.execute(
        "UPDATE queries SET status='Closed', closed_at=%s WHERE id=%s",
        (now, qid)
    )
    conn.commit()

st.title("Client Query Management System") # streamlit home page

menu = st.sidebar.selectbox("Menu", ["Login", "Signup"])

if menu == "Signup": # signup page
    st.subheader("Create Account")

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["Client", "Support"])

    if st.button("Signup"):
        signup(username, email, password, role)
        st.success("Account Created!")

elif menu == "Login": # login page
    st.subheader("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login(email, password)
        if user:
            st.session_state["user"] = user
            st.session_state["logged_in"] = True
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid Credentials")

if "logged_in" in st.session_state: # DASHBOARD
    user = st.session_state["user"]
    role = user[4]
    email = user[2]

    if st.sidebar.button("Logout"): # LOGOUT
        st.session_state.clear()
        st.rerun()

    if role == "Client": # client query dashboard
        st.header("Client Dashboard")

        st.subheader("Raise Query")
        title = st.text_input("Query Title")
        desc = st.text_area("Description")

        if st.button("Submit Query"):
            create_query(email, title, desc)
            st.success("Query Raised!")

        st.subheader("My Queries")
        queries = get_client_queries(email)

        for q in queries:
            st.write(f"ID: {q[0]}")
            st.write(f"Title: {q[2]}")
            st.write(f"Status: {q[4]}")
            st.write(f"Raised: {q[5]}")
            st.write(f"Closed: {q[6]}")
            st.write("---")

    elif role == "Support": # support team dashboard
        st.header("Support Dashboard")

        queries = get_all_queries()

         # DataFrame
        df = pd.DataFrame(queries, columns=[ 
            "id","email","title","desc","status","raised","closed"
        ])

        
        st.subheader("🟡 Open Queries") # display open query
        for q in queries:
            if q[4] == "Open":
                st.write(f"ID: {q[0]} | {q[2]} |\n{q[3]}")
                if st.button(f"Close {q[0]}"):
                    close_query(q[0])
                    st.rerun()

        
        st.subheader("🟢 Closed Queries") # display close query
        closed_df = df[df["status"] == "Closed"]
        st.dataframe(closed_df)

       
        st.subheader("Query Status Distribution") # visual of query status
        status_counts = df["status"].value_counts()

        fig1, ax1 = plt.subplots()
        ax1.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%')
        st.pyplot(fig1)

        
        st.subheader("Resolution Time Analysis") # visual of resolution time

        df_closed = df.dropna(subset=["closed"])

        if not df_closed.empty:
            df_closed["resolution_time"] = (
                df_closed["closed"] - df_closed["raised"]
            ).dt.total_seconds() / 60  # minutes

            avg_time = df_closed["resolution_time"].mean()
            fast = len(df_closed[df_closed["resolution_time"] < avg_time])
            slow = len(df_closed[df_closed["resolution_time"] >= avg_time])

            fig2, ax2 = plt.subplots()
            ax2.pie([fast, slow],
                    labels=["Fast", "Slow"],
                    autopct='%1.1f%%',
                    wedgeprops=dict(width=0.4))
            st.pyplot(fig2)

            st.subheader('Historical Data')
            csv_df = pd.read_csv(r"D:\obito\2026-04-09T11-59_export.csv")
            st.dataframe(csv_df)
