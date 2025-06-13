# Streamlit-based Web App for Farm Inventory Management (Connected Tabs + Google Sheets)

import streamlit as st
import pandas as pd
import uuid
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
import json
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    json.loads(st.secrets["credentials"]), scope
)
gc = gspread.authorize(credentials)

def get_worksheet(sheet_name):
    sh = gc.open("Farm Inventory Data")  # Must already exist in your Google Drive
    return sh.worksheet(sheet_name)

# --- App Initialization ---
def init_data():
    if "sowing" not in st.session_state:
        st.session_state.sowing = pd.DataFrame(columns=["Sowing_ID", "Date", "Crop", "Variety", "Field_ID", "Area_ha"])
    if "harvest" not in st.session_state:
        st.session_state.harvest = pd.DataFrame(columns=["Harvest_ID", "Sowing_ID", "Date", "Crop", "Variety", "Field_ID", "Harvested_kg"])
    if "processing1" not in st.session_state:
        st.session_state.processing1 = pd.DataFrame(columns=["Processing_ID", "Harvest_ID", "Date", "Crop", "Variety", "Field_ID", "Input_kg", "Output_Lint_kg", "Output_Raw_Seed_kg"])
    if "processing2" not in st.session_state:
        st.session_state.processing2 = pd.DataFrame(columns=["Processing_ID", "Processing1_ID", "Date", "Crop", "Variety", "Field_ID", "Input_kg", "Output_Graded_kg", "Output_Undersize_kg"])
    if "sales" not in st.session_state:
        st.session_state.sales = pd.DataFrame(columns=["Sale_ID", "Date", "Crop", "Variety", "Category", "Quantity_Sold_kg", "Price_per_kg", "Total_Income"])

init_data()

st.title("🌾 Farm Inventory Management System")

menu = st.sidebar.selectbox("Menu", ["Sowing", "Harvest", "Processing", "Sales", "Stock Summary"])

if menu == "Sowing":
    st.header("Add New Sowing Record")
    with st.form("sowing_form"):
        date = st.date_input("Sowing Date")
        crop = st.text_input("Crop")
        variety = st.text_input("Variety")
        field_id = st.text_input("Field ID")
        area = st.number_input("Area (ha)", min_value=0.0)
        submitted = st.form_submit_button("Add Sowing")
        if submitted:
            sow_id = str(uuid.uuid4())
            new_row = [sow_id, date, crop, variety, field_id, area]
            st.session_state.sowing.loc[len(st.session_state.sowing)] = new_row
            get_worksheet("Sowing").append_row([str(i) for i in new_row])
            st.success("Sowing record added and saved to Google Sheet.")
    st.dataframe(st.session_state.sowing)

elif menu == "Harvest":
    st.header("Add Harvest Record")
    with st.form("harvest_form"):
        sowing_ids = st.session_state.sowing["Sowing_ID"].tolist()
        selected = st.selectbox("Select Sowing ID", sowing_ids)
        harvest_date = st.date_input("Harvest Date")
        harvested_kg = st.number_input("Harvested Quantity (kg)", min_value=0.0)
        submitted = st.form_submit_button("Add Harvest")
        if submitted:
            sow_row = st.session_state.sowing[st.session_state.sowing["Sowing_ID"] == selected].iloc[0]
            h_id = str(uuid.uuid4())
            new_row = [h_id, selected, harvest_date, sow_row.Crop, sow_row.Variety, sow_row.Field_ID, harvested_kg]
            st.session_state.harvest.loc[len(st.session_state.harvest)] = new_row
            get_worksheet("Harvest").append_row([str(i) for i in new_row])
            st.success("Harvest record added and saved to Google Sheet.")
    st.dataframe(st.session_state.harvest)

elif menu == "Processing":
    st.header("Processing")
    tab1, tab2 = st.tabs(["Seed Cotton → Lint + Raw Seed", "Raw Seed → Graded + Undersize"])

    with tab1:
        with st.form("proc1_form"):
            harvest_ids = st.session_state.harvest["Harvest_ID"].tolist()
            selected = st.selectbox("Select Harvest ID", harvest_ids)
            date = st.date_input("Processing Date")
            input_kg = st.number_input("Seed Cotton Input (kg)", min_value=0.0)
            lint = st.number_input("Output Lint (kg)", min_value=0.0)
            raw_seed = st.number_input("Output Raw Seed (kg)", min_value=0.0)
            submitted = st.form_submit_button("Add Ginning Record")
            if submitted:
                h_row = st.session_state.harvest[st.session_state.harvest["Harvest_ID"] == selected].iloc[0]
                pid = str(uuid.uuid4())
                new_row = [pid, selected, date, h_row.Crop, h_row.Variety, h_row.Field_ID, input_kg, lint, raw_seed]
                st.session_state.processing1.loc[len(st.session_state.processing1)] = new_row
                get_worksheet("Processing1").append_row([str(i) for i in new_row])
                st.success("Ginning record added and saved to Google Sheet.")
        st.dataframe(st.session_state.processing1)

    with tab2:
        with st.form("proc2_form"):
            proc1_ids = st.session_state.processing1["Processing_ID"].tolist()
            selected = st.selectbox("Select Processing ID (Raw Seed)", proc1_ids)
            date = st.date_input("Processing Date")
            input_kg = st.number_input("Raw Seed Input (kg)", min_value=0.0)
            graded = st.number_input("Output Graded Seed (kg)", min_value=0.0)
            undersize = st.number_input("Output Undersize (kg)", min_value=0.0)
            submitted = st.form_submit_button("Add Grading Record")
            if submitted:
                p1_row = st.session_state.processing1[st.session_state.processing1["Processing_ID"] == selected].iloc[0]
                pid = str(uuid.uuid4())
                new_row = [pid, selected, date, p1_row.Crop, p1_row.Variety, p1_row.Field_ID, input_kg, graded, undersize]
                st.session_state.processing2.loc[len(st.session_state.processing2)] = new_row
                get_worksheet("Processing2").append_row([str(i) for i in new_row])
                st.success("Grading record added and saved to Google Sheet.")
        st.dataframe(st.session_state.processing2)

elif menu == "Sales":
    st.header("Add Sale Record")
    with st.form("sale_form"):
        date = st.date_input("Sale Date")
        crop = st.text_input("Crop")
        variety = st.text_input("Variety")
        category = st.selectbox("Category", ["Seed Cotton", "Lint", "Raw Seed", "Graded Seed", "Undersize"])
        qty = st.number_input("Quantity Sold (kg)", min_value=0.0)
        price = st.number_input("Price per kg (₹)", min_value=0.0)
        income = qty * price
        submitted = st.form_submit_button("Add Sale")
        if submitted:
            sale_id = str(uuid.uuid4())
            new_row = [sale_id, date, crop, variety, category, qty, price, income]
            st.session_state.sales.loc[len(st.session_state.sales)] = new_row
            get_worksheet("Sales").append_row([str(i) for i in new_row])
            st.success(f"Sale recorded. Income: ₹{income}. Saved to Google Sheet.")
    st.dataframe(st.session_state.sales)

elif menu == "Stock Summary":
    st.header("📦 Stock Summary")
    stock = {}
    for _, row in st.session_state.processing1.iterrows():
        key1 = (row["Crop"], row["Variety"], "Lint")
        key2 = (row["Crop"], row["Variety"], "Raw Seed")
        stock[key1] = stock.get(key1, 0) + row["Output_Lint_kg"]
        stock[key2] = stock.get(key2, 0) + row["Output_Raw_Seed_kg"]

    for _, row in st.session_state.processing2.iterrows():
        key1 = (row["Crop"], row["Variety"], "Graded Seed")
        key2 = (row["Crop"], row["Variety"], "Undersize")
        stock[key1] = stock.get(key1, 0) + row["Output_Graded_kg"]
        stock[key2] = stock.get(key2, 0) + row["Output_Undersize_kg"]

    for _, row in st.session_state.sales.iterrows():
        key = (row["Crop"], row["Variety"], row["Category"])
        stock[key] = stock.get(key, 0) - row["Quantity_Sold_kg"]

    summary = pd.DataFrame([{"Crop": k[0], "Variety": k[1], "Category": k[2], "Remaining Stock (kg)": v} for k, v in stock.items()])
    st.dataframe(summary)

    st.markdown("---")
    st.subheader("💰 Income Summary")
    income_summary = st.session_state.sales.groupby(["Crop", "Variety", "Category"])["Total_Income"].sum().reset_index()
    st.dataframe(income_summary)
