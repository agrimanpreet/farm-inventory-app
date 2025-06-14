# farm_inventory_app/app.py

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets connection
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(st.secrets["credentials"], scopes=scope)
client = gspread.authorize(credentials)
sheet = client.open("Farm Inventory Data")

# Load sheets
def get_df(tab_name):
    try:
        return pd.DataFrame(sheet.worksheet(tab_name).get_all_records())
    except:
        return pd.DataFrame()

def append_row(tab_name, row):
    sheet.worksheet(tab_name).append_row(row)

sowing_df = get_df("Sowing")
harvest_df = get_df("Harvest")
processing1_df = get_df("Processing1")
processing2_df = get_df("Processing2")
sales_df = get_df("Sales")

# Unique crop and variety lists
def unique_values(df, column):
    return sorted(df[column].dropna().unique()) if column in df.columns else []

crop_list = unique_values(sowing_df, "Crop")
variety_list = unique_values(sowing_df, "Variety")

st.title("Farm Inventory Manager")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Sowing", "Harvest", "Processing 1", "Processing 2", "Sales", "Summary"])

with tab1:
    st.header("Sowing Entry")
    with st.form("sowing_form"):
        field_id = st.text_input("Field ID")
        crop = st.text_input("Crop (new or existing)")
        variety = st.text_input("Variety")
        area = st.number_input("Area (acres)", min_value=0.0, format="%.2f")
        date = st.date_input("Sowing Date")
        submitted = st.form_submit_button("Add Sowing Entry")
        if submitted:
            append_row("Sowing", [field_id, crop, variety, area, str(date)])
            st.success("Sowing record added.")

with tab2:
    st.header("Harvest Entry")
    with st.form("harvest_form"):
        date = st.date_input("Harvest Date")
        crop = st.selectbox("Crop", crop_list)
        variety = st.selectbox("Variety", variety_list)
        produce_type = st.text_input("Produce Type (e.g., Seed Cotton, Raw Seed, Grain, etc.)")
        quantity = st.number_input("Quantity (kg)", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Add Harvest Entry")
        if submitted:
            append_row("Harvest", [str(date), crop, variety, produce_type, quantity])
            st.success("Harvest entry added.")

with tab3:
    st.header("Processing Stage 1: Seed Cotton ➜ Lint + Raw Seed")
    with st.form("processing1_form"):
        crop = st.selectbox("Crop", crop_list, key="p1crop")
        variety = st.selectbox("Variety", variety_list, key="p1variety")
        seed_cotton_input = st.number_input("Input Seed Cotton (kg)", min_value=0.0, format="%.2f")

        total_available = harvest_df.query("Crop == @crop and Variety == @variety and Produce_Type == 'Seed Cotton'")["Quantity"].sum()
        used_so_far = processing1_df.query("Crop == @crop and Variety == @variety")["Seed_Cotton_Input"].sum()
        remaining = total_available - used_so_far
        st.info(f"Available Seed Cotton: {remaining:.2f} kg")

        if seed_cotton_input > remaining:
            st.error("Input exceeds available Seed Cotton")
        else:
            lint_output = st.number_input("Lint Quantity (kg)", min_value=0.0, format="%.2f")
            raw_seed_output = st.number_input("Raw Seed Quantity (kg)", min_value=0.0, format="%.2f")
            submitted = st.form_submit_button("Add Processing 1 Entry")
            if submitted:
                append_row("Processing1", [crop, variety, seed_cotton_input, lint_output, raw_seed_output])
                st.success("Processing Stage 1 entry added.")

with tab4:
    st.header("Processing Stage 2: Raw Seed ➜ Graded + Undersize")
    with st.form("processing2_form"):
        crop = st.selectbox("Crop", crop_list, key="p2crop")
        variety = st.selectbox("Variety", variety_list, key="p2variety")
        raw_seed_input = st.number_input("Input Raw Seed (kg)", min_value=0.0, format="%.2f")

        from_harvest = harvest_df.query("Crop == @crop and Variety == @variety and Produce_Type == 'Raw Seed'")["Quantity"].sum()
        from_processing1 = processing1_df.query("Crop == @crop and Variety == @variety")["Raw_Seed_Output"].sum()
        used_in_processing2 = processing2_df.query("Crop == @crop and Variety == @variety")["Raw_Seed_Input"].sum()
        total_available_raw_seed = from_harvest + from_processing1 - used_in_processing2

        st.info(f"Available Raw Seed: {total_available_raw_seed:.2f} kg")

        if raw_seed_input > total_available_raw_seed:
            st.error("Input exceeds available Raw Seed")
        else:
            graded_output = st.number_input("Graded Seed Quantity (kg)", min_value=0.0, format="%.2f")
            undersize_output = st.number_input("Undersize Quantity (kg)", min_value=0.0, format="%.2f")
            submitted = st.form_submit_button("Add Processing 2 Entry")
            if submitted:
                append_row("Processing2", [crop, variety, raw_seed_input, graded_output, undersize_output])
                st.success("Processing Stage 2 entry added.")

with tab5:
    st.header("Sales Entry")
    with st.form("sales_form"):
        date = st.date_input("Sale Date")
        crop = st.selectbox("Crop", crop_list, key="salescrop")
        variety = st.selectbox("Variety", variety_list, key="salesvariety")
        item_type = st.selectbox("Item Type", ["Seed Cotton", "Lint", "Raw Seed", "Graded Seed", "Undersize", "Grain"])
        quantity = st.number_input("Quantity Sold (kg)", min_value=0.0, format="%.2f")
        price_per_kg = st.number_input("Price per kg (₹)", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Add Sale Entry")
        if submitted:
            income = quantity * price_per_kg
            append_row("Sales", [str(date), crop, variety, item_type, quantity, price_per_kg, income])
            st.success("Sale entry added.")

with tab6:
    st.header("Inventory and Income Summary")

    inventory = {}
    for tab in ["Harvest", "Processing1", "Processing2"]:
        df = get_df(tab)
        for _, row in df.iterrows():
            key = (row.get("Crop"), row.get("Variety"))
            if key not in inventory:
                inventory[key] = {"Seed Cotton": 0, "Lint": 0, "Raw Seed": 0, "Graded Seed": 0, "Undersize": 0}

    for _, row in harvest_df.iterrows():
        key = (row["Crop"], row["Variety"])
        inventory[key][row["Produce_Type"]] += row["Quantity"]

    for _, row in processing1_df.iterrows():
        key = (row["Crop"], row["Variety"])
        inventory[key]["Seed Cotton"] -= row["Seed_Cotton_Input"]
        inventory[key]["Lint"] += row["Lint_Output"]
        inventory[key]["Raw Seed"] += row["Raw_Seed_Output"]

    for _, row in processing2_df.iterrows():
        key = (row["Crop"], row["Variety"])
        inventory[key]["Raw Seed"] -= row["Raw_Seed_Input"]
        inventory[key]["Graded Seed"] += row["Graded_Seed_Output"]
        inventory[key]["Undersize"] += row["Undersize_Output"]

    for _, row in sales_df.iterrows():
        key = (row["Crop"], row["Variety"])
        inventory[key][row["Item_Type"]] -= row["Quantity"]

    st.subheader("Stock Inventory")
    st.dataframe(pd.DataFrame.from_dict(inventory, orient="index").fillna(0))

    st.subheader("Total Income")
    total_income = sales_df["Income"].sum() if "Income" in sales_df else 0
    st.metric(label="Total Income (₹)", value=f"₹{total_income:,.2f}")
