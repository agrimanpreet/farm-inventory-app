import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from datetime import datetime

# Set up Google Sheets credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["credentials"], scopes=scope
)
client = gspread.authorize(credentials)

# Open your Google Sheet
sheet = client.open("Farm Inventory")

# Helper function to update sheet
def append_row(sheet_name, row):
    worksheet = sheet.worksheet(sheet_name)
    worksheet.append_row(row)

st.title("🌾 Farm Inventory Management")

menu = ["Sowing", "Harvest", "Processing 1", "Processing 2", "Sales", "Summary"]
choice = st.sidebar.selectbox("Select Operation", menu)

if choice == "Sowing":
    st.subheader("🌱 Add Sowing Record")
    with st.form("sowing_form"):
        sowing_id = st.text_input("Sowing ID")
        date = st.date_input("Sowing Date", value=datetime.today())
        crop = st.selectbox("Crop", ["Cotton", "Wheat", "Mustard"])
        variety = st.text_input("Variety")
        area = st.number_input("Area (acres)", min_value=0.0)
        field_id = st.text_input("Field ID")
        submitted = st.form_submit_button("Add Record")

        if submitted:
            row = [sowing_id, str(date), crop, variety, area, field_id]
            append_row("Sowing", row)
            st.success("✅ Sowing record added!")

elif choice == "Harvest":
    st.subheader("🌾 Add Harvest Record")
    with st.form("harvest_form"):
        sowing_id = st.text_input("Sowing ID (from sowing tab)")
        date = st.date_input("Harvest Date", value=datetime.today())
        produce_type = st.selectbox("Produce Type", ["Seed Cotton", "Wheat Grain", "Mustard Seed"])
        quantity = st.number_input("Quantity (kg)", min_value=0.0)
        submitted = st.form_submit_button("Add Record")

        if submitted:
            row = [sowing_id, str(date), produce_type, quantity]
            append_row("Harvest", row)
            st.success("✅ Harvest record added!")

elif choice == "Processing 1":
    st.subheader("🏗️ Processing - Stage 1 (e.g., Seed Cotton ➜ Lint + Raw Seed)")
    with st.form("processing1_form"):
        harvest_id = st.text_input("Harvest Batch ID")
        input_type = st.text_input("Input Produce Type")
        output_1 = st.text_input("Output 1 Type")
        qty_1 = st.number_input("Quantity Output 1 (kg)", min_value=0.0)
        output_2 = st.text_input("Output 2 Type")
        qty_2 = st.number_input("Quantity Output 2 (kg)", min_value=0.0)
        submitted = st.form_submit_button("Add Record")

        if submitted:
            row = [harvest_id, input_type, output_1, qty_1, output_2, qty_2]
            append_row("Processing1", row)
            st.success("✅ Processing Stage 1 record added!")

elif choice == "Processing 2":
    st.subheader("🔬 Processing - Stage 2 (e.g., Raw Seed ➜ Graded + Undersize)")
    with st.form("processing2_form"):
        batch_id = st.text_input("Input Batch ID")
        input_type = st.text_input("Input Type")
        graded_qty = st.number_input("Graded Seed Quantity (kg)", min_value=0.0)
        undersize_qty = st.number_input("Undersize Quantity (kg)", min_value=0.0)
        submitted = st.form_submit_button("Add Record")

        if submitted:
            row = [batch_id, input_type, graded_qty, undersize_qty]
            append_row("Processing2", row)
            st.success("✅ Processing Stage 2 record added!")

elif choice == "Sales":
    st.subheader("💰 Record Sales")
    with st.form("sales_form"):
        item = st.text_input("Item Sold")
        date = st.date_input("Date of Sale", value=datetime.today())
        quantity = st.number_input("Quantity Sold (kg)", min_value=0.0)
        price = st.number_input("Price per kg (₹)", min_value=0.0)
        income = quantity * price
        submitted = st.form_submit_button("Record Sale")

        if submitted:
            row = [item, str(date), quantity, price, income]
            append_row("Sales", row)
            st.success(f"✅ Sale recorded! Income: ₹{income:.2f}")

elif choice == "Summary":
    st.subheader("📊 Inventory & Income Summary")
    sales_df = pd.DataFrame(sheet.worksheet("Sales").get_all_records())
    if not sales_df.empty:
        total_income = sales_df["income"].sum()
        st.metric("💰 Total Income (₹)", f"₹{total_income:,.2f}")
        st.dataframe(sales_df)
    else:
        st.info("No sales data available.")
