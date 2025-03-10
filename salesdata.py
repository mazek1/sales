import streamlit as st
import pandas as pd
import os
import re
import bcrypt
import matplotlib.pyplot as plt

# Sideoverskrift
st.title("Sales Data Dashboard")

DATA_FILE = "saved_sales_data.csv"

# Simpel bruger-login med hashed adgangskoder
USERS = {
    "anette@soft-rebels.com": {"name": "Anette Elsebet Pedersen", "password": bcrypt.hashpw("password1".encode(), bcrypt.gensalt()), "access_all": False},
    "sælger2@example.com": {"name": "Sælger 2", "password": bcrypt.hashpw("password2".encode(), bcrypt.gensalt()), "access_all": False},
    "marianne@soft-rebels.com": {"name": "Marianne", "password": bcrypt.hashpw("adminpass".encode(), bcrypt.gensalt()), "access_all": True},
    "mads@soft-rebels.com": {"name": "Mads", "password": bcrypt.hashpw("adminpass".encode(), bcrypt.gensalt()), "access_all": True}
}

# Login-sektion
st.sidebar.header("Login")
email = st.sidebar.text_input("Indtast din e-mail for at logge ind")
password = st.sidebar.text_input("Indtast din adgangskode", type="password")

if email not in USERS or not bcrypt.checkpw(password.encode(), USERS[email]["password"]):
    st.sidebar.warning("Ugyldig e-mail eller adgangskode. Prøv igen.")
    st.stop()

sælger_navn = USERS[email]["name"]
adgang_alle = USERS[email]["access_all"]
st.sidebar.success(f"Logget ind som: {sælger_navn}")

# Indlæs tidligere gemt data, hvis den eksisterer
if os.path.exists(DATA_FILE):
    try:
        df = pd.read_csv(DATA_FILE, sep=';', encoding='utf-8', low_memory=False, on_bad_lines='warn')
    except pd.errors.ParserError:
        df = pd.read_csv(DATA_FILE, sep=',', encoding='utf-8', low_memory=False, on_bad_lines='warn')
    if "Invoice Date" in df.columns:
        df["Invoice Date"] = pd.to_datetime(df["Invoice Date"], errors='coerce')
else:
    df = None

# Kun admins kan uploade CSV-filer
if adgang_alle:
    uploaded_file = st.file_uploader("Upload CSV-fil med salgsdata", type=["csv"])
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8', low_memory=False, on_bad_lines='warn')
        except pd.errors.ParserError:
            df = pd.read_csv(uploaded_file, sep=',', encoding='utf-8', low_memory=False, on_bad_lines='warn')
    except pd.errors.ParserError:
        df = pd.read_csv(uploaded_file, sep=',', encoding='utf-8', low_memory=False, on_bad_lines='warn')
        df.to_csv(DATA_FILE, index=False)
        st.success("CSV-fil er blevet uploadet og indlæst!")

# Filtrer data for sælgeren
if df is not None and not adgang_alle and "Salesperson" in df.columns:
    df["Salesperson"] = df["Salesperson"].astype(str).str.lower().str.strip()
    sælger_navn_clean = sælger_navn.lower().strip()
    df = df[df["Salesperson"] == sælger_navn_clean]
    
if df is not None:
    st.write("Data efter filtrering:")
    st.dataframe(df)
    
    # Valg af periode (uge/måned)
    periode_valg = st.selectbox("Vælg periode", ["Månedlig", "Ugentlig"])
    
    df["Sales Price"] = pd.to_numeric(df["Sales Price"], errors="coerce")
    df_sorted = df.sort_values(by="Invoice Date")
    
    if periode_valg == "Månedlig":
        df_sorted["Periode"] = df_sorted["Invoice Date"].dt.to_period("M")
    else:
        df_sorted["Periode"] = df_sorted["Invoice Date"].dt.to_period("W")
    
    total_sales_over_time = df_sorted.groupby("Periode")["Sales Price"].sum()
    
    if total_sales_over_time.empty:
        st.warning("Ingen salgsdata tilgængelig for denne periode.")
    else:
        fig, ax = plt.subplots()
        total_sales_over_time.plot(kind="line", ax=ax)
        ax.set_title("Total Sales Over Time")
        ax.set_ylabel("Sales (DKK)")
        ax.set_xlabel("Periode")
        st.pyplot(fig)
    
    # Opret en oversigt over total salg
    total_sales = df["Sales Price"].sum()
    st.metric(label="Total Sales", value=f"{total_sales:.2f} DKK" if isinstance(total_sales, (int, float)) and not pd.isna(total_sales) else "0.00 DKK")
