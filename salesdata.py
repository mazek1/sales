import streamlit as st
import pandas as pd

# Sideoverskrift
st.title("Salgsdata Dashboard")

# Upload CSV-fil
uploaded_file = st.file_uploader("Upload CSV-fil med salgsdata", type=["csv"])

if uploaded_file:
    # Indlæs data med semikolon som separator
    df = pd.read_csv(uploaded_file, sep=";", low_memory=False)
    
    # Konverter datokolonner
    if "Invoice Date" in df.columns:
        df["Invoice Date"] = pd.to_datetime(df["Invoice Date"], errors='coerce')
    
    # Filtreringssektion
    st.sidebar.header("Filtrér data")

    kunde_filter = st.sidebar.text_input("Søg efter kunde")
    season_filter = st.sidebar.selectbox("Vælg season", ["Alle"] + sorted(df["Season"].dropna().unique().tolist()))
    style_no_filter = st.sidebar.text_input("Søg efter Style No.")
    style_name_filter = st.sidebar.text_input("Søg efter Style Name")
    color_filter = st.sidebar.text_input("Søg efter Color")

    # Filtrer data baseret på input
    filtered_df = df.copy()
    if kunde_filter:
        filtered_df = filtered_df[filtered_df["Customer Name"].str.contains(kunde_filter, case=False, na=False)]
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

    # Generer link til sælgerne (dummy placeholder)
    st.write("### Del dette dashboard med dine sælgere:")
    st.code("https://your-streamlit-app-url")
