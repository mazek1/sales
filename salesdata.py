import streamlit as st
import pandas as pd
import os
import re
import bcrypt

# Sideoverskrift
st.title("Salgsdata Dashboard")

DATA_FILE = "saved_sales_data.csv"

# Simpel bruger-login med hashed adgangskoder
USERS = {
    "anette@soft-rebels.com": {"name": "Anette Elsebet Pedersen", "password": bcrypt.hashpw("password1".encode(), bcrypt.gensalt()), "access_all": False},
    "sælger2@example.com": {"name": "Sælger 2", "password": bcrypt.hashpw("password2".encode(), bcrypt.gensalt()), "access_all": False},
    "marianne@soft-rebels.com": {"name": "Marianne", "password": bcrypt.hashpw("adminpass".encode(), bcrypt.gensalt()), "access_all": True},
    "mads@soft-rebels.com": {"name": "Mads", "password": bcrypt.hashpw("adminpass".encode(), bcrypt.gensalt()), "access_all": True}
}

# UI til brugerhåndtering (kun for admin)
def admin_user_management():
    st.sidebar.subheader("Brugerhåndtering")
    if email in USERS and USERS[email]["access_all"]:
        action = st.sidebar.selectbox("Vælg handling", ["Tilføj bruger", "Slet bruger", "Se brugere"])
        
        if action == "Tilføj bruger":
            new_email = st.sidebar.text_input("Ny bruger e-mail")
            new_name = st.sidebar.text_input("Navn")
            new_password = st.sidebar.text_input("Adgangskode", type="password")
            access_all = st.sidebar.checkbox("Giv adgang til alle kunder")
            
            if st.sidebar.button("Opret bruger"):
                USERS[new_email] = {"name": new_name, "password": bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()), "access_all": access_all}
                st.sidebar.success(f"Bruger {new_email} oprettet!")
        
        elif action == "Slet bruger":
            user_to_delete = st.sidebar.selectbox("Vælg bruger", list(USERS.keys()))
            if st.sidebar.button("Slet bruger"):
                if user_to_delete != "admin@example.com":
                    del USERS[user_to_delete]
                    st.sidebar.success(f"Bruger {user_to_delete} er slettet.")
                else:
                    st.sidebar.error("Admin-brugeren kan ikke slettes.")
        
        elif action == "Se brugere":
            st.sidebar.write(pd.DataFrame.from_dict({k: {"name": v["name"], "access_all": v["access_all"]} for k, v in USERS.items()}, orient="index"))

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
admin_user_management()

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_csv(uploaded_file, sep=";", low_memory=False)
    
    # Behold kun de relevante kolonner, hvis de findes
    relevant_columns = ["Customer Name", "Season", "Style No", "Style Name", "Color", "Invoice Date", "Physical Size Quantity Delivered", "Sales Price", "Sales Price Original", "Salesperson"]
    df = df[[col for col in relevant_columns if col in df.columns]]
    
    # Fjern =" og " fra Style No
    df["Style No"] = df["Style No"].astype(str).apply(lambda x: re.sub(r'^[="\s]+|["\s]+$', '', x))
    
    # Konverter datokolonner
    if "Invoice Date" in df.columns:
        df["Invoice Date"] = pd.to_datetime(df["Invoice Date"], errors='coerce')
    
    # Konverter priser til numeriske værdier og håndter fejl
    for col in ["Sales Price", "Sales Price Original"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Beregn rabat, hvis kolonnerne eksisterer
    if "Sales Price" in df.columns and "Sales Price Original" in df.columns:
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
    if "Invoice Date" in df.columns:
        df["Invoice Date"] = pd.to_datetime(df["Invoice Date"], errors='coerce')
else:
    df = None

if df is not None:
    # Filtrér data, så sælger kun ser sine egne kunder (medmindre de har adgang til alle)
    if "Salesperson" in df.columns and not adgang_alle:
        df["Salesperson"] = df["Salesperson"].astype(str).str.lower().str.strip()
        sælger_navn_clean = sælger_navn.lower().strip()
        st.write("Unikke sælgernavne i CSV:", df["Salesperson"].unique())
df = df[df["Salesperson"] == sælger_navn_clean]
    
    if df.empty:
        st.warning(f"Ingen data fundet for '{sælger_navn}'. Tjek at 'Salesperson'-kolonnen i CSV-filen matcher nøjagtigt dette navn.")
