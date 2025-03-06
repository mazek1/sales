import streamlit as st
import pandas as pd
import os
import re

# Sideoverskrift
st.title("Salgsdata Dashboard")

DATA_FILE = "saved_sales_data.csv"

# Simpel bruger-login (kan udvides med en database eller API)
USERS = {
    "anette@soft-rebels.com": {"name": "Anette Pedersen", "password": "password1", "access_all": False},
    "sælger2@example.com": {"name": "Sælger 2", "password": "password2", "access_all": False},
    "marianne@soft-rebels.com": {"name": "Admin", "password": "adminpass", "access_all": True}
}

# Login-sektion
st.sidebar.header("Login")
email = st.sidebar.text_input("Indtast din e-mail for at logge ind")
password = st.sidebar.text_input("Indtast din adgangskode", type="password")

if email not in USERS or USERS[email]["password"] != password:
    st.sidebar.warning("Ugyldig e-mail eller adgangskode. Prøv igen.")
    st.stop()

sælger_navn = USERS[email]["name"]
adgang_alle = USERS[email]["access_all"]
st.sidebar.success(f"Logget ind som: {sælger_navn}")

@st.cache_data
def load_data(uploaded_file):
    # Indlæs data med semikolon som separator
    df = pd.read_csv(uploaded_file, sep=";", low_memory=False)
    
    # Behold kun de relevante kolonner
    columns_to_keep = ["Customer Name", "Season", "Style No", "Style Name", "Color", "Invoice Date", "Physical Size Quantity Delivered", "Sales Price", "Sales Price Original", "Salesperson"]
    df = df[columns_to_keep]
    
    # Fjern =" og " fra Style No
    df["Style No"] = df["Style No"].astype(str).apply(lambda x: re.sub(r'^[="\s]+|["\s]+$', '', x))
    
    # Konverter datokolonner
    df["Invoice Date"] = pd.to_datetime(df["Invoice Date"], errors='coerce')
    
    # Konverter priser til numeriske værdier og håndter fejl
    df["Sales Price"] = pd.to_numeric(df["Sales Price"], errors='coerce')
    df["Sales Price Original"] = pd.to_numeric(df["Sales Price Original"], errors='coerce')
    
    # Beregn rabat
    df["Discount Applied"] = df["Sales Price Original"] - df["Sales Price"]
    df["Discount Applied"] = df["Discount Applied"].fillna(0)
    df["Discount %"] = (df["Discount Applied"] / df["Sales Price Original"]) * 100
    df["Discount %"] = df["Discount %"].fillna(0).round(2)
    
    # Gem data til fil
    df.to_csv(DATA_FILE, index=False)
    
    return df

# Tjek om tidligere data eksisterer
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df["Invoice Date"] = pd.to_datetime(df["Invoice Date"], errors='coerce')
else:
    df = None

# Upload CSV-fil
uploaded_file = st.file_uploader("Upload CSV-fil med salgsdata", type=["csv"])

if uploaded_file:
    df = load_data(uploaded_file)

# Tilføj knap til at rydde gemt data
if st.button("Ryd gemt data"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        st.write("### Gemt data er blevet slettet. Upload en ny fil for at fortsætte.")
        df = None

if df is not None:
    # Filtrér data, så sælger kun ser sine egne kunder (medmindre de har adgang til alle)
    if not adgang_alle:
        df = df[df["Salesperson"] == sælger_navn]
    
    # Filtreringssektion
    st.sidebar.header("Filtrér data")

    kunde_filter = st.sidebar.selectbox("Vælg kunde", ["Alle"] + sorted(df["Customer Name"].dropna().unique().tolist()))
    season_filter = st.sidebar.selectbox("Vælg season", ["Alle"] + sorted(df["Season"].dropna().unique().tolist()))
    style_no_filter = st.sidebar.text_input("Søg efter Style No.")
    style_name_filter = st.sidebar.text_input("Søg efter Style Name")
    color_filter = st.sidebar.text_input("Søg efter Color")

    # Filtrer data baseret på input
    filtered_df = df.copy()
    if kunde_filter != "Alle":
        filtered_df = filtered_df[filtered_df["Customer Name"] == kunde_filter]
    if season_filter != "Alle":
        filtered_df = filtered_df[filtered_df["Season"] == season_filter]
    if style_no_filter:
        filtered_df = filtered_df[filtered_df["Style No"].astype(str).str.contains(style_no_filter, case=False, na=False)]
    if style_name_filter:
        filtered_df = filtered_df[filtered_df["Style Name"].str.contains(style_name_filter, case=False, na=False)]
    if color_filter:
        filtered_df = filtered_df[filtered_df["Color"].str.contains(color_filter, case=False, na=False)]

    # Vis tabel
    st.write("### Filtrerede salgsdata")
    st.dataframe(filtered_df)
    
    # Valgfri: Vis en graf over salgstrends
    if "Invoice Date" in filtered_df.columns and "Physical Size Quantity Delivered" in filtered_df.columns:
        sales_trend = filtered_df.groupby("Invoice Date")["Physical Size Quantity Delivered"].sum()
        st.write("### Salgstrend over tid")
        st.line_chart(sales_trend)

    # Generer link til sælgerne
    st.write("### Del dette dashboard med dine sælgere:")
    st.code("https://salesdatapy-bgsd78qzbbpzn38ja4d73w.streamlit.app/")
