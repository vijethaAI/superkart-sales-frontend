"""
SuperKart Sales Forecasting - Frontend
----------------------------------------
A Streamlit app that provides a simple UI on top of the Flask backend API,
supporting both single-record ("online") inference and batch (CSV upload)
inference.

The backend URL is read from the BACKEND_URL environment variable (set this
as a secret/variable on your Hugging Face Space once the backend Space is
deployed and you have its public URL), falling back to localhost for local
testing.
"""

import os
import io
import requests
import pandas as pd
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:7860")

st.set_page_config(page_title="SuperKart Sales Forecast", page_icon="🛒", layout="centered")

st.title("🛒 SuperKart Sales Forecasting")
st.caption("Predict Product_Store_Sales_Total for a product-store combination.")
st.write(f"Connected backend: `{BACKEND_URL}`")

tab_single, tab_batch = st.tabs(["🔹 Single Prediction", "📄 Batch Prediction"])

# ---------------------------------------------------------------------------
# TAB 1: Single (online) prediction
# ---------------------------------------------------------------------------
with tab_single:
    st.subheader("Enter product & store details")

    col1, col2 = st.columns(2)
    with col1:
        product_weight = st.number_input("Product Weight", min_value=0.0, max_value=30.0, value=12.5, step=0.1)
        product_allocated_area = st.number_input("Product Allocated Area (ratio)", min_value=0.0, max_value=1.0, value=0.05, step=0.001, format="%.3f")
        product_mrp = st.number_input("Product MRP", min_value=0.0, max_value=500.0, value=147.0, step=0.5)
        product_id_char = st.selectbox("Product Id Prefix", ["FD", "DR", "NC"], help="FD = Food, DR = Drinks, NC = Non-Consumable")
        product_sugar_content = st.selectbox("Product Sugar Content", ["Low Sugar", "Regular", "No Sugar"])

    with col2:
        store_size = st.selectbox("Store Size", ["High", "Medium", "Small"])
        store_location_city_type = st.selectbox("Store Location City Type", ["Tier 1", "Tier 2", "Tier 3"])
        store_type = st.selectbox("Store Type", ["Supermarket Type1", "Supermarket Type2", "Departmental Store", "Food Mart"])
        store_age_years = st.number_input("Store Age (years)", min_value=0, max_value=100, value=15, step=1)
        product_type_category = st.selectbox("Product Type Category", ["Perishables", "Non Perishables"])

    if st.button("Predict Sales", type="primary"):
        payload = {
            "Product_Weight": product_weight,
            "Product_Sugar_Content": product_sugar_content,
            "Product_Allocated_Area": product_allocated_area,
            "Product_MRP": product_mrp,
            "Store_Size": store_size,
            "Store_Location_City_Type": store_location_city_type,
            "Store_Type": store_type,
            "Product_Id_char": product_id_char,
            "Store_Age_Years": store_age_years,
            "Product_Type_Category": product_type_category,
        }
        try:
            resp = requests.post(f"{BACKEND_URL}/predict", json=payload, timeout=30)
            if resp.status_code == 200:
                result = resp.json()
                st.success(f"Predicted Product_Store_Sales_Total: **{result['prediction']:,}**")
            else:
                st.error(f"Backend returned an error: {resp.json().get('error', resp.text)}")
        except requests.exceptions.RequestException as e:
            st.error(f"Could not reach backend API: {e}")

# ---------------------------------------------------------------------------
# TAB 2: Batch prediction via CSV upload
# ---------------------------------------------------------------------------
with tab_batch:
    st.subheader("Upload a CSV file for batch prediction")
    st.write(
        "The CSV must contain exactly these columns: "
        "`Product_Weight, Product_Sugar_Content, Product_Allocated_Area, Product_MRP, "
        "Store_Size, Store_Location_City_Type, Store_Type, Product_Id_char, "
        "Store_Age_Years, Product_Type_Category`"
    )

    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    if uploaded_file is not None:
        try:
            batch_df = pd.read_csv(uploaded_file)
            st.write("Preview of uploaded data:")
            st.dataframe(batch_df.head())

            if st.button("Run Batch Prediction"):
                records = batch_df.to_dict(orient="records")
                resp = requests.post(f"{BACKEND_URL}/batch_predict", json={"records": records}, timeout=60)

                if resp.status_code == 200:
                    result = resp.json()
                    batch_df["Predicted_Sales"] = result["predictions"]
                    st.success(f"Generated {result['count']} predictions.")
                    st.dataframe(batch_df)

                    csv_buffer = io.StringIO()
                    batch_df.to_csv(csv_buffer, index=False)
                    st.download_button(
                        label="Download predictions as CSV",
                        data=csv_buffer.getvalue(),
                        file_name="superkart_batch_predictions.csv",
                        mime="text/csv"
                    )
                else:
                    st.error(f"Backend returned an error: {resp.json().get('error', resp.text)}")
        except Exception as e:
            st.error(f"Could not process the uploaded file: {e}")
