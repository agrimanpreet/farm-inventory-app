# farm_inventory_app/app.py
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets API setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(st.secrets["credentials"], scopes=scope)
client = gspread.authorize(credentials)

# Open the spreadsheet
sheet = client.open("Farm Inventory Data")

def load_sheet(sheet_name):
    try:
        df = pd.DataFrame(sheet.worksheet(sheet_name).get_all_records())
        df.columns = df.columns.str.strip()
        return df
    except Exception:
        return pd.DataFrame()

def save_to_sheet(sheet_name, data):
    try:
        worksheet = sheet.worksheet(sheet_name)
    except:
        worksheet = sheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
    existing_data = worksheet.get_all_records()
    updated_df = pd.DataFrame(existing_data + [data])
    worksheet.clear()
    worksheet.update([updated_df.columns.values.tolist()] + updated_df.values.tolist())

# Tabs
st.set_page_config(layout="wide")
tabs = st.tabs(["Sowing", "Harvest", "Processing 1", "Processing 2", "Sales", "Inventory Summary"])

# --- SOWING TAB ---
sowing_df = load_sheet("Sowing")
with tabs[0]:
    st.header("Sowing Entry")
    with st.form("sowing_form"):
        field_id = st.text_input("Field ID")
        crop = st.text_input("Crop")
        variety = st.text_input("Variety")
        area = st.number_input("Area (acres)", min_value=0.0, step=0.1)
        sowing_date = st.date_input("Sowing Date")
        submit = st.form_submit_button("Submit")
    if submit:
        sowing_data = {
            "Field_ID": field_id,
            "Crop": crop,
            "Variety": variety,
            "Area": area,
            "Sowing_Date": sowing_date.strftime("%Y-%m-%d")
        }
        save_to_sheet("Sowing", sowing_data)
        st.success("Sowing data saved successfully!")

# --- HARVEST TAB ---
harvest_df = load_sheet("Harvest")
with tabs[1]:
    st.header("Harvest Entry")
    crop_options = sowing_df["Crop"].unique().tolist()
    crop = st.selectbox("Crop", crop_options)
    variety = st.selectbox("Variety", sowing_df[sowing_df["Crop"] == crop]["Variety"].unique())
    with st.form("harvest_form"):
        harvest_date = st.date_input("Harvest Date")
        produce_type = st.text_input("Produce Type (e.g., Seed Cotton, Raw Seed, Grain, etc.)")
        quantity = st.number_input("Quantity (kg)", min_value=0.0, step=1.0)
        submit = st.form_submit_button("Submit")
    if submit:
        harvest_data = {
            "Crop": crop,
            "Variety": variety,
            "Harvest_Date": harvest_date.strftime("%Y-%m-%d"),
            "Produce_Type": produce_type,
            "Quantity": quantity
        }
        save_to_sheet("Harvest", harvest_data)
        st.success("Harvest data saved successfully!")

# --- PROCESSING 1 TAB ---
data_p1 = load_sheet("Processing1")
with tabs[2]:
    st.header("Processing 1: Seed Cotton to Lint + Raw Seed")
    crop = st.selectbox("Crop", harvest_df["Crop"].unique())
    variety = st.selectbox("Variety", harvest_df[harvest_df["Crop"] == crop]["Variety"].unique())
    total_available = harvest_df.query("Crop == @crop and Variety == @variety and Produce_Type == 'Seed Cotton'")["Quantity"].sum()
    processed = data_p1.query("Crop == @crop and Variety == @variety")
    already_processed = processed["Seed_Cotton_Quantity"].sum() if not processed.empty else 0
    remaining = total_available - already_processed
    st.info(f"Total available seed cotton: {total_available} kg | Already processed: {already_processed} kg | Remaining: {remaining} kg")

    with st.form("proc1_form"):
        seed_cotton_qty = st.number_input("Seed Cotton Quantity (kg)", min_value=0.0, max_value=remaining, step=1.0)
        lint_qty = st.number_input("Lint Quantity (kg)", min_value=0.0, max_value=seed_cotton_qty, step=1.0)
        raw_seed_qty = seed_cotton_qty - lint_qty
        st.write(f"Calculated Raw Seed Quantity: {raw_seed_qty:.2f} kg")
        submit = st.form_submit_button("Submit")
    if submit:
        data = {
            "Crop": crop,
            "Variety": variety,
            "Seed_Cotton_Quantity": seed_cotton_qty,
            "Lint_Quantity": lint_qty,
            "Raw_Seed_Quantity": raw_seed_qty
        }
        save_to_sheet("Processing1", data)
        st.success("Processing 1 data saved successfully!")

# --- PROCESSING 2 TAB ---
data_p2 = load_sheet("Processing2")
with tabs[3]:
    st.header("Processing 2: Raw Seed to Graded + Undersized")
    crop = st.selectbox("Crop", harvest_df["Crop"].unique(), key="p2")
    variety = st.selectbox("Variety", harvest_df[harvest_df["Crop"] == crop]["Variety"].unique(), key="v2")
    raw_from_harvest = harvest_df.query("Crop == @crop and Variety == @variety and Produce_Type == 'Raw Seed'")["Quantity"].sum()
    raw_from_proc1 = data_p1.query("Crop == @crop and Variety == @variety")["Raw_Seed_Quantity"].sum()
    total_raw = raw_from_harvest + raw_from_proc1
    used_raw = data_p2.query("Crop == @crop and Variety == @variety")["Raw_Seed_Used"].sum()
    remaining_raw = total_raw - used_raw
    st.info(f"Total Raw Seed: {total_raw} kg | Already Used: {used_raw} kg | Remaining: {remaining_raw} kg")

    with st.form("proc2_form"):
        raw_used = st.number_input("Raw Seed Used (kg)", min_value=0.0, max_value=remaining_raw, step=1.0)
        graded_seed = st.number_input("Graded Seed (kg)", min_value=0.0, max_value=raw_used, step=1.0)
        undersize = raw_used - graded_seed
        st.write(f"Calculated Undersize Seed: {undersize:.2f} kg")
        submit = st.form_submit_button("Submit")
    if submit:
        data = {
            "Crop": crop,
            "Variety": variety,
            "Raw_Seed_Used": raw_used,
            "Graded_Seed": graded_seed,
            "Undersize": undersize
        }
        save_to_sheet("Processing2", data)
        st.success("Processing 2 data saved successfully!")

# --- SALES TAB ---
sales_df = load_sheet("Sales")
with tabs[4]:
    st.header("Sales Entry")
    crop = st.selectbox("Crop", sowing_df["Crop"].unique(), key="sales")
    variety = st.selectbox("Variety", sowing_df[sowing_df["Crop"] == crop]["Variety"].unique(), key="sales2")
    with st.form("sales_form"):
        product_type = st.text_input("Product Type (e.g., Lint, Graded Seed, etc.)")
        quantity = st.number_input("Quantity Sold (kg)", min_value=0.0, step=1.0)
        price = st.number_input("Price per kg", min_value=0.0, step=1.0)
        income = quantity * price
        st.write(f"Calculated Income: ₹{income:.2f}")
        submit = st.form_submit_button("Submit")
    if submit:
        data = {
            "Crop": crop,
            "Variety": variety,
            "Product_Type": product_type,
            "Quantity": quantity,
            "Price_per_kg": price,
            "Income": income
        }
        save_to_sheet("Sales", data)
        st.success("Sales data saved successfully!")

# --- INVENTORY SUMMARY ---
with tabs[5]:
    st.header("Inventory Summary")
    st.subheader("Raw and Processed Stock")
    st.dataframe(harvest_df.groupby(["Crop", "Variety", "Produce_Type"]).sum(numeric_only=True).reset_index())
    st.subheader("Processing 1 Summary")
    st.dataframe(data_p1.groupby(["Crop", "Variety"]).sum(numeric_only=True).reset_index())
    st.subheader("Processing 2 Summary")
    st.dataframe(data_p2.groupby(["Crop", "Variety"]).sum(numeric_only=True).reset_index())
    st.subheader("Sales Summary")
    st.dataframe(sales_df.groupby(["Crop", "Variety", "Product_Type"]).sum(numeric_only=True).reset_index())
