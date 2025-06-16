import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials

# Authenticate and connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(credentials)

sheet = client.open("Farm Inventory Data")

# Utility functions
def load_sheet(name):
    try:
        data = sheet.worksheet(name).get_all_records()
        df = pd.DataFrame(data)
        df.columns = df.columns.str.strip().str.title()
        return df
    except Exception as e:
        st.error(f"Failed to load {name} sheet: {e}")
        return pd.DataFrame()

def save_to_sheet(sheet_name, data):
    try:
        worksheet = sheet.worksheet(sheet_name)
        worksheet.clear()
        worksheet.update([data.columns.tolist()] + data.values.tolist())
    except Exception as e:
        st.error(f"Failed to save to {sheet_name}: {e}")

# Load all sheets
sowing_df = load_sheet("Sowing")
harvest_df = load_sheet("Harvest")
processing1_df = load_sheet("Processing1")
processing2_df = load_sheet("Processing2")
sales_df = load_sheet("Sales")

# Tabs
st.title("Farm Inventory Management")
tab = st.sidebar.radio("Go to", ["Sowing", "Harvest", "Processing 1", "Processing 2", "Sales", "Inventory Summary"])

if tab == "Sowing":
    st.header("Sowing Entry")
    field_id = st.text_input("Field ID")
    crop = st.text_input("Crop")
    variety = st.text_input("Variety")
    area = st.number_input("Area (acres)", min_value=0.0)
    sowing_date = st.date_input("Sowing Date")

    if st.button("Add Sowing Record"):
        new_entry = pd.DataFrame([{"Field ID": field_id, "Crop": crop, "Variety": variety, "Area": area, "Sowing Date": str(sowing_date)}])
        updated_df = pd.concat([sowing_df, new_entry], ignore_index=True)
        save_to_sheet("Sowing", updated_df)
        st.success("Sowing record added successfully.")

elif tab == "Harvest":
    st.header("Harvest Entry")
    crop_options = sowing_df["Crop"].unique() if not sowing_df.empty else []
    crop = st.selectbox("Crop", crop_options)

    variety_options = sowing_df[sowing_df["Crop"] == crop]["Variety"].unique() if crop else []
    variety = st.selectbox("Variety", variety_options)

    produce_type = st.text_input("Produce Type (e.g., Seed Cotton, Grain, Raw Seed)")
    quantity = st.number_input("Quantity (kg)", min_value=0.0)
    harvest_date = st.date_input("Harvest Date")

    if st.button("Add Harvest Record"):
        new_entry = pd.DataFrame([{"Crop": crop, "Variety": variety, "Produce Type": produce_type, "Quantity": quantity, "Harvest Date": str(harvest_date)}])
        updated_df = pd.concat([harvest_df, new_entry], ignore_index=True)
        save_to_sheet("Harvest", updated_df)
        st.success("Harvest record added successfully.")

elif tab == "Processing 1":
    st.header("Processing 1: Seed Cotton Processing")
    crop = st.selectbox("Crop", harvest_df["Crop"].unique())
    variety = st.selectbox("Variety", harvest_df[harvest_df["Crop"] == crop]["Variety"].unique())

    total_available = harvest_df.query("Crop == @crop and Variety == @variety and `Produce Type` == 'Seed Cotton'")["Quantity"].sum()
    processed = processing1_df.query("Crop == @crop and Variety == @variety")["Seed Cotton Quantity"].sum()
    available = total_available - processed

    st.info(f"Available Seed Cotton: {available:.2f} kg")
    input_qty = st.number_input("Seed Cotton Quantity (kg)", min_value=0.0, max_value=available)

    lint_qty = st.number_input("Lint Quantity (kg)", min_value=0.0, max_value=input_qty)
    raw_seed_qty = input_qty - lint_qty
    st.write(f"Raw Seed Quantity auto-calculated: {raw_seed_qty:.2f} kg")

    if st.button("Submit Processing 1"):
        new_entry = pd.DataFrame([{"Crop": crop, "Variety": variety, "Seed Cotton Quantity": input_qty, "Lint Quantity": lint_qty, "Raw Seed Quantity": raw_seed_qty}])
        updated_df = pd.concat([processing1_df, new_entry], ignore_index=True)
        save_to_sheet("Processing1", updated_df)
        st.success("Processing 1 record added successfully.")

elif tab == "Processing 2":
    st.header("Processing 2: Raw Seed Processing")
    crop = st.selectbox("Crop", sowing_df["Crop"].unique())
    variety = st.selectbox("Variety", sowing_df[sowing_df["Crop"] == crop]["Variety"].unique())

    harvest_raw = harvest_df.query("Crop == @crop and Variety == @variety and `Produce Type` == 'Raw Seed'")["Quantity"].sum()
    from_processing1 = processing1_df.query("Crop == @crop and Variety == @variety")["Raw Seed Quantity"].sum()
    total_raw_seed = harvest_raw + from_processing1
    used = processing2_df.query("Crop == @crop and Variety == @variety")["Raw Seed Quantity"].sum()
    available = total_raw_seed - used

    st.info(f"Available Raw Seed: {available:.2f} kg")
    input_qty = st.number_input("Raw Seed Quantity (kg)", min_value=0.0, max_value=available)

    graded_qty = st.number_input("Graded Seed Quantity (kg)", min_value=0.0, max_value=input_qty)
    undersize_qty = input_qty - graded_qty
    st.write(f"Undersize Quantity auto-calculated: {undersize_qty:.2f} kg")

    if st.button("Submit Processing 2"):
        new_entry = pd.DataFrame([{"Crop": crop, "Variety": variety, "Raw Seed Quantity": input_qty, "Graded Seed Quantity": graded_qty, "Undersize Quantity": undersize_qty}])
        updated_df = pd.concat([processing2_df, new_entry], ignore_index=True)
        save_to_sheet("Processing2", updated_df)
        st.success("Processing 2 record added successfully.")

elif tab == "Sales":
    st.header("Sales Entry")
    crop = st.selectbox("Crop", sowing_df["Crop"].unique())
    variety = st.selectbox("Variety", sowing_df[sowing_df["Crop"] == crop]["Variety"].unique())
    produce_type = st.text_input("Produce Type")
    quantity = st.number_input("Quantity Sold (kg)", min_value=0.0)
    amount = st.number_input("Sale Amount (Rs)", min_value=0.0)
    sale_date = st.date_input("Sale Date")

    if st.button("Submit Sale"):
        new_entry = pd.DataFrame([{"Crop": crop, "Variety": variety, "Produce Type": produce_type, "Quantity": quantity, "Amount": amount, "Sale Date": str(sale_date)}])
        updated_df = pd.concat([sales_df, new_entry], ignore_index=True)
        save_to_sheet("Sales", updated_df)
        st.success("Sale record added successfully.")

elif tab == "Inventory Summary":
    st.header("Inventory Summary")
    st.subheader("Harvested But Unprocessed")
    harvest_summary = harvest_df.groupby(["Crop", "Variety", "Produce Type"])["Quantity"].sum().reset_index()
    processed1_summary = processing1_df.groupby(["Crop", "Variety"])["Seed Cotton Quantity"].sum().reset_index()
    processed2_summary = processing2_df.groupby(["Crop", "Variety"])["Raw Seed Quantity"].sum().reset_index()

    st.subheader("Processed Outputs")
    st.write("**Processing 1:**")
    st.dataframe(processing1_df)
    st.write("**Processing 2:**")
    st.dataframe(processing2_df)

    st.subheader("Sales Summary")
    st.dataframe(sales_df)
