import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Authenticate and connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(
    st.secrets["credentials"], scopes=scope
)
client = gspread.authorize(credentials)
sheet = client.open("Farm Inventory Data")

# Load all worksheets
sowing_ws = sheet.worksheet("Sowing")
harvest_ws = sheet.worksheet("Harvest")
processing1_ws = sheet.worksheet("Processing1")
processing2_ws = sheet.worksheet("Processing2")
sales_ws = sheet.worksheet("Sales")

# Read data into dataframes
sowing_df = pd.DataFrame(sowing_ws.get_all_records())
harvest_df = pd.DataFrame(harvest_ws.get_all_records())
processing1_df = pd.DataFrame(processing1_ws.get_all_records())
processing2_df = pd.DataFrame(processing2_ws.get_all_records())
sales_df = pd.DataFrame(sales_ws.get_all_records())

st.title("🌾 Farm Inventory Management")

# Navigation
menu = ["Sowing", "Harvest", "Processing 1", "Processing 2", "Sales", "Inventory Summary", "Income Summary"]
tab = st.sidebar.radio("Navigate", menu)

if tab == "Sowing":
    st.subheader("Add Sowing Record")
    with st.form("sowing_form"):
        field_id = st.text_input("Field ID")
        crop = st.text_input("Crop")
        variety = st.text_input("Variety")
        area = st.number_input("Area (acres)", min_value=0.0)
        date = st.date_input("Sowing Date")
        submitted = st.form_submit_button("Submit")
    if submitted:
        row = [field_id, crop, variety, area, str(date)]
        sowing_ws.append_row(row)
        st.success("Sowing record added!")

if tab == "Harvest":
    st.subheader("Add Harvest Record")
    with st.form("harvest_form"):
        date = st.date_input("Harvest Date")
        crop = st.selectbox("Crop", sowing_df["Crop"].unique())
        variety = st.selectbox("Variety", sowing_df[sowing_df["Crop"] == crop]["Variety"].unique())
        produce_type = st.text_input("Produce Type")
        qty = st.number_input("Quantity (kg)", min_value=0.0)
        submitted = st.form_submit_button("Submit")
    if submitted:
        row = [str(date), crop, variety, produce_type, qty]
        harvest_ws.append_row(row)
        st.success("Harvest record added!")

if tab == "Processing 1":
    st.subheader("Processing: Seed Cotton → Lint + Raw Seed")
    with st.form("proc1_form"):
        crop = st.selectbox("Crop", harvest_df["Crop"].unique())
        variety = st.selectbox("Variety", harvest_df[harvest_df["Crop"] == crop]["Variety"].unique())
        seed_cotton_qty = st.number_input("Seed Cotton Input (kg)", min_value=0.0)
        lint_qty = st.number_input("Lint Output (kg)", min_value=0.0)
        raw_seed_qty = st.number_input("Raw Seed Output (kg)", min_value=0.0)
        submitted = st.form_submit_button("Submit")
    if submitted:
        available = harvest_df.query("Crop == @crop and Variety == @variety and Produce_Type == 'Seed Cotton'")["Quantity"].sum()
        used = processing1_df.query("Crop == @crop and Variety == @variety")["Seed_Cotton_Input"].sum()
        remaining = available - used
        if seed_cotton_qty > remaining:
            st.error(f"Only {remaining:.2f} kg Seed Cotton available.")
        else:
            row = [crop, variety, seed_cotton_qty, lint_qty, raw_seed_qty]
            processing1_ws.append_row(row)
            st.success("Processing 1 record added!")

if tab == "Processing 2":
    st.subheader("Processing: Raw Seed → Graded + Undersize")
    with st.form("proc2_form"):
        crop = st.selectbox("Crop", harvest_df["Crop"].unique())
        variety = st.selectbox("Variety", harvest_df[harvest_df["Crop"] == crop]["Variety"].unique())
        raw_seed_input = st.number_input("Raw Seed Input (kg)", min_value=0.0)
        graded = st.number_input("Graded Seed (kg)", min_value=0.0)
        undersize = st.number_input("Undersize (kg)", min_value=0.0)
        submitted = st.form_submit_button("Submit")
    if submitted:
        harvested_raw = harvest_df.query("Crop == @crop and Variety == @variety and Produce_Type == 'Raw Seed'")["Quantity"].sum()
        from_proc1 = processing1_df.query("Crop == @crop and Variety == @variety")["Raw_Seed_Output"].sum()
        total_raw = harvested_raw + from_proc1
        used = processing2_df.query("Crop == @crop and Variety == @variety")["Raw_Seed_Input"].sum()
        remaining = total_raw - used
        if raw_seed_input > remaining:
            st.error(f"Only {remaining:.2f} kg Raw Seed available.")
        else:
            row = [crop, variety, raw_seed_input, graded, undersize]
            processing2_ws.append_row(row)
            st.success("Processing 2 record added!")

if tab == "Sales":
    st.subheader("Add Sales Record")
    with st.form("sales_form"):
        date = st.date_input("Sale Date")
        crop = st.selectbox("Crop", sowing_df["Crop"].unique())
        variety = st.selectbox("Variety", sowing_df[sowing_df["Crop"] == crop]["Variety"].unique())
        product = st.selectbox("Product", ["Graded Seed", "Undersize", "Grain", "Lint"])
        qty = st.number_input("Quantity Sold (kg)", min_value=0.0)
        rate = st.number_input("Rate (₹/kg)", min_value=0.0)
        submitted = st.form_submit_button("Submit")
    if submitted:
        row = [str(date), crop, variety, product, qty, rate, qty * rate]
        sales_ws.append_row(row)
        st.success("Sales record added!")

if tab == "Inventory Summary":
    st.subheader("Inventory Summary")
    inv1 = harvest_df.groupby(["Crop", "Variety", "Produce_Type"])["Quantity"].sum().reset_index()
    inv1 = inv1.rename(columns={"Quantity": "Total Harvested"})
    inv2 = processing1_df.groupby(["Crop", "Variety"])["Seed_Cotton_Input"].sum().reset_index()
    inv3 = processing2_df.groupby(["Crop", "Variety"])["Raw_Seed_Input"].sum().reset_index()
    st.write("### Harvested Stock")
    st.dataframe(inv1)
    st.write("### Processing 1 Input")
    st.dataframe(inv2)
    st.write("### Processing 2 Input")
    st.dataframe(inv3)

if tab == "Income Summary":
    st.subheader("Income Summary")
    if not sales_df.empty:
        summary = sales_df.groupby(["Crop", "Variety", "Product"])["Total Income"].sum().reset_index()
        st.dataframe(summary)
    else:
        st.info("No sales data found.")
