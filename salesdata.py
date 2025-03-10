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

# UI til brugerhåndtering (kun for admin)
def admin_user_management():
    if email in USERS and USERS[email]["access_all"]:
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

# Indlæs tidligere gemt data, hvis den eksisterer
if os.path.exists(DATA_FILE) and not adgang_alle:
    df = pd.read_csv(DATA_FILE)
    if "Invoice Date" in df.columns:
        df["Invoice Date"] = pd.to_datetime(df["Invoice Date"], errors='coerce')
else:
    df = None

# Kun admins kan uploade CSV-filer
if adgang_alle:
    uploaded_file = st.file_uploader("Upload CSV-fil med salgsdata", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file, sep=";", low_memory=False)
        df.to_csv(DATA_FILE, index=False)
        st.success("CSV-fil er blevet uploadet og indlæst!")

# Filtrer data for sælgeren

# Opret en graf over total salg over tid
if df is not None:
    st.subheader("Total Sales Over Time")
    df_sorted = df.sort_values(by="Invoice Date")
    total_sales_over_time = df_sorted.groupby("Invoice Date")["Sales Price"].sum()
    if total_sales_over_time.empty:
        st.warning("Ingen salgsdata tilgængelig for denne periode.")
    else:
    fig, ax = plt.subplots()
    total_sales_over_time.plot(kind="line", ax=ax)
    ax.set_title("Total Sales Over Time")
    ax.set_ylabel("Sales (DKK)")
    ax.set_xlabel("Date")
    st.pyplot(fig)

    # Valg af specifik kunde
    selected_customer = st.selectbox("Vælg kunde", ["Alle kunder"] + sorted(df["Customer Name"].unique()))
    
    if selected_customer != "Alle kunder":
        df_customer = df[df["Customer Name"] == selected_customer]
        total_sales_customer = df_customer.groupby("Invoice Date")["Sales Price"].sum()
        if total_sales_customer.empty:
            st.warning(f"Ingen salg registreret for {selected_customer} i denne periode.")
        else:
        fig, ax = plt.subplots()
        total_sales_customer.plot(kind="line", ax=ax)
        ax.set_title(f"Sales Over Time for {selected_customer}")
        ax.set_ylabel("Sales (DKK)")
        ax.set_xlabel("Date")
        st.pyplot(fig)
if df is not None and not adgang_alle:
    df["Salesperson"] = df["Salesperson"].astype(str).str.lower().str.strip()
    df["Salesperson"] = df["Salesperson"].replace({'\\r': '', '\\n': ''}, regex=True)
    df = df.dropna(subset=["Salesperson"])
    sælger_navn_clean = sælger_navn.lower().strip()
    
    if sælger_navn_clean in df["Salesperson"].unique():
        st.write(f"Data fundet for {sælger_navn_clean}")
        df = df[df["Salesperson"] == sælger_navn_clean]
        st.write("Data efter filtrering:")
        st.write(df.head())
        
                
        # Opret en oversigt over total salg
        total_sales = df["Sales Price"].sum()
        st.metric(label="Total Sales", value=f"{total_sales:.2f} DKK" if isinstance(total_sales, (int, float)) and not pd.isna(total_sales) else "0.00 DKK")
        
    else:
        st.warning(f"Ingen salg fundet for '{sælger_navn}'. Enten er der ingen salg registreret, eller navnet matcher ikke præcist i CSV.")
