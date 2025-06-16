# Farm Inventory Management App with Full Interconnectivity
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Farm Inventory Manager", layout="wide")

# Connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(st.secrets["credentials"], scopes=scope)
client = gspread.authorize(credentials)
sheet = client.open("Farm Inventory Data")

# Utility: Load a worksheet as a DataFrame
def load_sheet(name):
    try:
        return pd.DataFrame(sheet.worksheet(name).get_all_records())
    except:
        return pd.DataFrame()

# Utility: Append row to a worksheet
def append_row(name, row):
    sheet.worksheet(name).append_row(row)

# Load existing data
data_sowing = load_sheet("Sowing")
data_harvest = load_sheet("Harvest")
data_p1 = load_sheet("Processing1")
data_p2 = load_sheet("Processing2")
data_sales = load_sheet("Sales")

st.title("Farm Inventory Management App")
tabs = st.tabs(["Sowing", "Harvest", "Processing 1", "Processing 2", "Sales", "Inventory Summary"])

# ----------------- SOWING TAB -----------------
with tabs[0]:
    st.header("Sowing Entry")
    with st.form("sowing_form"):
        field_id = st.text_input("Field ID")
        crop = st.text_input("Crop")
        variety = st.text_input("Variety")
        area = st.number_input("Area (acres)", min_value=0.0)
        sowing_date = st.date_input("Sowing Date")
        submitted = st.form_submit_button("Submit")
        if submitted:
            append_row("Sowing", [field_id, crop, variety, area, str(sowing_date)])
            st.success("Sowing data added.")

# Extract crop/variety options for dropdowns
crop_options = sorted(data_sowing["Crop"].unique()) if not data_sowing.empty else []
def get_variety_options(crop):
    return sorted(data_sowing[data_sowing["Crop"] == crop]["Variety"].unique()) if crop in crop_options else []

# ----------------- HARVEST TAB -----------------
with tabs[1]:
    st.header("Harvest Entry")
    with st.form("harvest_form"):
        harvest_date = st.date_input("Harvest Date")
        crop = st.selectbox("Crop", crop_options)
        variety = st.selectbox("Variety", get_variety_options(crop))
        produce_type = st.selectbox("Produce Type", ["Seed Cotton", "Raw Seed", "Grain", "Other"])
        quantity = st.number_input("Quantity (kg)", min_value=0.0)
        submitted = st.form_submit_button("Submit")
        if submitted:
            append_row("Harvest", [str(harvest_date), crop, variety, produce_type, quantity])
            st.success("Harvest entry recorded.")

# ----------------- PROCESSING 1 -----------------
with tabs[2]:
    st.header("Processing 1: Seed Cotton to Lint + Raw Seed")
    with st.form("proc1_form"):
        crop = st.selectbox("Crop", crop_options, key="p1_crop")
        variety = st.selectbox("Variety", get_variety_options(crop), key="p1_variety")

        # Filter available stock from harvest
        harvested = data_harvest.query("Crop == @crop and Variety == @variety and Produce_Type == 'Seed Cotton'")
        total_seed_cotton = harvested["Quantity"].sum()
        processed = data_p1.query("Crop == @crop and Variety == @variety")
        already_processed = processed["Seed_Cotton_Input"].sum() if not processed.empty else 0
        available = total_seed_cotton - already_processed

        st.info(f"Available Seed Cotton: {available:.2f} kg")
        seed_cotton = st.number_input("Input Seed Cotton (kg)", min_value=0.0, max_value=available)
        lint = st.number_input("Output Lint (kg)", min_value=0.0, max_value=seed_cotton)
        raw_seed = seed_cotton - lint
        st.write(f"Auto-calculated Raw Seed: {raw_seed:.2f} kg")
        submitted = st.form_submit_button("Submit")
        if submitted:
            append_row("Processing1", [crop, variety, seed_cotton, lint, raw_seed])
            st.success("Processing 1 entry recorded.")

# ----------------- PROCESSING 2 -----------------
with tabs[3]:
    st.header("Processing 2: Raw Seed to Graded + Undersize")
    with st.form("proc2_form"):
        crop = st.selectbox("Crop", crop_options, key="p2_crop")
        variety = st.selectbox("Variety", get_variety_options(crop), key="p2_variety")

        # Calculate available raw seed
        from_harvest = data_harvest.query("Crop == @crop and Variety == @variety and Produce_Type == 'Raw Seed'")["Quantity"].sum()
        from_p1 = data_p1.query("Crop == @crop and Variety == @variety")["Raw_Seed_Output"].sum() if not data_p1.empty else 0
        used = data_p2.query("Crop == @crop and Variety == @variety")["Raw_Seed_Input"].sum() if not data_p2.empty else 0
        available_raw = from_harvest + from_p1 - used

        st.info(f"Available Raw Seed: {available_raw:.2f} kg")
        raw_seed_input = st.number_input("Input Raw Seed (kg)", min_value=0.0, max_value=available_raw)
        graded = st.number_input("Graded Seed (kg)", min_value=0.0, max_value=raw_seed_input)
        undersize = raw_seed_input - graded
        st.write(f"Auto-calculated Undersize: {undersize:.2f} kg")
        submitted = st.form_submit_button("Submit")
        if submitted:
            append_row("Processing2", [crop, variety, raw_seed_input, graded, undersize])
            st.success("Processing 2 entry recorded.")

# ----------------- SALES TAB -----------------
with tabs[4]:
    st.header("Sales Entry")
    with st.form("sales_form"):
        date = st.date_input("Sale Date")
        crop = st.selectbox("Crop", crop_options, key="sale_crop")
        variety = st.selectbox("Variety", get_variety_options(crop), key="sale_variety")
        product = st.selectbox("Product", ["Graded Seed", "Lint", "Grain", "Other"])
        quantity = st.number_input("Sold Quantity (kg)", min_value=0.0)
        price = st.number_input("Price (₹/kg)", min_value=0.0)
        income = quantity * price
        st.write(f"Estimated Income: ₹{income:.2f}")
        submitted = st.form_submit_button("Submit")
        if submitted:
            append_row("Sales", [str(date), crop, variety, product, quantity, price, income])
            st.success("Sale recorded.")

# ----------------- INVENTORY SUMMARY -----------------
with tabs[5]:
    st.header("Inventory Summary")
    if not data_harvest.empty:
        summary = data_harvest.groupby(["Crop", "Variety", "Produce_Type"])["Quantity"].sum().reset_index()
        st.subheader("Total Harvested")
        st.dataframe(summary)
        st.download_button("Download Harvest Summary", summary.to_csv(index=False), file_name="harvest_summary.csv")

    if not data_p1.empty:
        st.subheader("Processing 1 Outputs")
        st.dataframe(data_p1)
    if not data_p2.empty:
        st.subheader("Processing 2 Outputs")
        st.dataframe(data_p2)
    if not data_sales.empty:
        st.subheader("Sales Summary")
        st.dataframe(data_sales)
        total_income = data_sales["Income"].sum()
        st.success(f"Total Income: ₹{total_income:.2f}")
