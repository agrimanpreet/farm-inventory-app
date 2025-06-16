import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="Farm Inventory App", layout="wide")

# ------------------- AUTHENTICATION -------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = Credentials.from_service_account_info(
    st.secrets["credentials"], scopes=scope
)

client = gspread.authorize(credentials)
sheet = client.open("Farm Inventory Data")

# ------------------- UTILITIES -------------------
def load_sheet(name):
    try:
        data = pd.DataFrame(sheet.worksheet(name).get_all_records())
        for col in data.columns:
            data[col] = data[col].astype(str).str.strip()
        return data
    except Exception as e:
        st.warning(f"Failed to load {name} sheet: {e}")
        return pd.DataFrame()

def save_to_sheet(name, new_data):
    try:
        worksheet = sheet.worksheet(name)
        existing_data = pd.DataFrame(worksheet.get_all_records())
        updated_df = pd.concat([existing_data, pd.DataFrame([new_data])], ignore_index=True)
        worksheet.update([updated_df.columns.values.tolist()] + updated_df.values.tolist())
    except Exception as e:
        st.error(f"Failed to save data to {name} sheet: {e}")

# ------------------- LOAD DATA -------------------
sowing_df = load_sheet("Sowing")
harvest_df = load_sheet("Harvest")
processing1_df = load_sheet("Processing1")
processing2_df = load_sheet("Processing2")
sales_df = load_sheet("Sales")

# ------------------- SOWING TAB -------------------
st.title("Farm Inventory Management")
tab = st.sidebar.radio("Select Tab", ["Sowing", "Harvest", "Processing 1", "Processing 2", "Sales", "Inventory Summary"])

if tab == "Sowing":
    st.header("Sowing Entry")
    field_id = st.text_input("Field ID")
    crop = st.text_input("Crop")
    variety = st.text_input("Variety")
    sowing_date = st.date_input("Sowing Date", value=datetime.today())
    area = st.number_input("Area (acres)", min_value=0.0, format="%.2f")

    if st.button("Submit Sowing"):
        if crop and variety:
            sowing_data = {
                "Field_ID": field_id,
                "Crop": crop.strip(),
                "Variety": variety.strip(),
                "Sowing_Date": sowing_date.strftime("%Y-%m-%d"),
                "Area": area
            }
            save_to_sheet("Sowing", sowing_data)
            st.success("Sowing entry saved!")
        else:
            st.warning("Please fill in all fields.")

# ------------------- HARVEST TAB -------------------
elif tab == "Harvest":
    st.header("Harvest Entry")
    crop_list = sowing_df["Crop"].unique() if not sowing_df.empty else []
    variety_list = sowing_df["Variety"].unique() if not sowing_df.empty else []

    crop = st.selectbox("Crop", crop_list)
    variety = st.selectbox("Variety", variety_list)
    harvest_date = st.date_input("Harvest Date", value=datetime.today())
    produce_type = st.text_input("Produce Type (e.g., Seed Cotton, Grain, Raw Seed)")
    quantity = st.number_input("Quantity (kg)", min_value=0.0, format="%.2f")

    if st.button("Submit Harvest"):
        harvest_data = {
            "Crop": crop,
            "Variety": variety,
            "Harvest_Date": harvest_date.strftime("%Y-%m-%d"),
            "Produce_Type": produce_type.strip(),
            "Quantity": quantity
        }
        save_to_sheet("Harvest", harvest_data)
        st.success("Harvest entry saved!")

# ------------------- PROCESSING 1 -------------------
elif tab == "Processing 1":
    st.header("Processing 1 (Seed Cotton → Lint + Raw Seed)")
    crop = st.selectbox("Crop", harvest_df["Crop"].unique())
    variety = st.selectbox("Variety", harvest_df["Variety"].unique())

    # Compute total available seed cotton
    available = harvest_df[
        (harvest_df["Crop"] == crop) &
        (harvest_df["Variety"] == variety) &
        (harvest_df["Produce_Type"].str.lower() == "seed cotton")
    ]["Quantity"].astype(float).sum()

    st.write(f"Available Seed Cotton: {available:.2f} kg")

    input_qty = st.number_input("Input Seed Cotton Quantity (kg)", min_value=0.0, max_value=available, format="%.2f")
    lint_qty = st.number_input("Lint Quantity (kg)", min_value=0.0, max_value=input_qty, format="%.2f")
    raw_seed_qty = input_qty - lint_qty

    if st.button("Submit Processing 1"):
        processing_data = {
            "Crop": crop,
            "Variety": variety,
            "Input_Seed_Cotton": input_qty,
            "Lint": lint_qty,
            "Raw_Seed": raw_seed_qty
        }
        save_to_sheet("Processing1", processing_data)
        st.success("Processing 1 entry saved!")

# ------------------- PROCESSING 2 -------------------
elif tab == "Processing 2":
    st.header("Processing 2 (Raw Seed → Graded + Undersize)")
    crop = st.selectbox("Crop", harvest_df["Crop"].unique())
    variety = st.selectbox("Variety", harvest_df["Variety"].unique())

    from_harvest = harvest_df[
        (harvest_df["Crop"] == crop) &
        (harvest_df["Variety"] == variety) &
        (harvest_df["Produce_Type"].str.lower() == "raw seed")
    ]["Quantity"].astype(float).sum()

    from_proc1 = processing1_df[
        (processing1_df["Crop"] == crop) &
        (processing1_df["Variety"] == variety)
    ]["Raw_Seed"].astype(float).sum()

    total_available = from_harvest + from_proc1
    st.write(f"Available Raw Seed: {total_available:.2f} kg")

    input_qty = st.number_input("Input Raw Seed Quantity (kg)", min_value=0.0, max_value=total_available, format="%.2f")
    graded_qty = st.number_input("Graded Seed (kg)", min_value=0.0, max_value=input_qty, format="%.2f")
    undersize_qty = input_qty - graded_qty

    if st.button("Submit Processing 2"):
        data = {
            "Crop": crop,
            "Variety": variety,
            "Input_Raw_Seed": input_qty,
            "Graded_Seed": graded_qty,
            "Undersize": undersize_qty
        }
        save_to_sheet("Processing2", data)
        st.success("Processing 2 entry saved!")

# ------------------- SALES TAB -------------------
elif tab == "Sales":
    st.header("Sales Entry")
    crop = st.selectbox("Crop", sowing_df["Crop"].unique())
    variety = st.selectbox("Variety", sowing_df["Variety"].unique())
    produce_type = st.text_input("Produce Type")
    quantity = st.number_input("Quantity Sold (kg)", min_value=0.0, format="%.2f")
    price = st.number_input("Price per kg (INR)", min_value=0.0, format="%.2f")
    total = quantity * price

    if st.button("Submit Sale"):
        data = {
            "Crop": crop,
            "Variety": variety,
            "Produce_Type": produce_type,
            "Quantity": quantity,
            "Price_per_kg": price,
            "Total_Value": total
        }
        save_to_sheet("Sales", data)
        st.success("Sale entry saved!")

# ------------------- INVENTORY SUMMARY -------------------
elif tab == "Inventory Summary":
    st.header("Inventory Summary")

    st.subheader("Harvest Summary")
    st.dataframe(harvest_df.groupby(["Crop", "Variety", "Produce_Type"])["Quantity"].sum().reset_index())

    st.subheader("Processing Summary")
    st.dataframe(processing1_df)
    st.dataframe(processing2_df)

    st.subheader("Sales Summary")
    st.dataframe(sales_df)
