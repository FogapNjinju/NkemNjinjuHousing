import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
from PIL import Image

# Define file paths
tenants_file = "tenants.csv"
payments_file = "payments.csv"
costs_file = "costs.csv"
receipts_folder = "receipts"

# Initialize CSV files and folders if not present
def init_files():
    if not os.path.exists(tenants_file):
        pd.DataFrame(columns=["Tenant ID", "Name", "Apartment", "Phone", "Location", "Registration Date"]).to_csv(tenants_file, index=False)
    if not os.path.exists(payments_file):
        pd.DataFrame(columns=["Tenant ID", "Month", "Amount", "Date", "Receipt", "Location"]).to_csv(payments_file, index=False)
    if not os.path.exists(costs_file):
        pd.DataFrame(columns=["Apartment", "Location", "Cost Type", "Amount", "Description", "Date", "Receipt"]).to_csv(costs_file, index=False)
    if not os.path.exists(receipts_folder):
        os.makedirs(receipts_folder)

init_files()

# Utility Functions
def load_data():
    tenants = pd.read_csv(tenants_file)
    payments = pd.read_csv(payments_file)
    costs = pd.read_csv(costs_file)
    return tenants, payments, costs

def save_tenant(tenant_id, name, apartment, phone, location):
    tenants = pd.read_csv(tenants_file)
    registration_date = datetime.datetime.now().strftime("%Y-%m")
    new_tenant = pd.DataFrame([{
        "Tenant ID": tenant_id,
        "Name": name,
        "Apartment": apartment,
        "Phone": phone,
        "Location": location,
        "Registration Date": registration_date
    }])
    tenants = pd.concat([tenants, new_tenant], ignore_index=True)
    tenants.to_csv(tenants_file, index=False)

def save_payment(tenant_id, start_month, num_months, amount_per_month, receipt_img, location):
    payments = pd.read_csv(payments_file)
    receipt_path = ""
    if receipt_img is not None:
        receipt_filename = f"{tenant_id}_{start_month}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        receipt_path = os.path.join(receipts_folder, receipt_filename)
        with open(receipt_path, "wb") as f:
            f.write(receipt_img.getbuffer())

    start_date = datetime.datetime.strptime(start_month, "%Y-%m")
    new_payments = []
    for i in range(num_months):
        month = (start_date + pd.DateOffset(months=i)).strftime("%Y-%m")
        new_payments.append({
            "Tenant ID": tenant_id,
            "Month": month,
            "Amount": amount_per_month,
            "Date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "Receipt": receipt_path,
            "Location": location
        })
    payments = pd.concat([payments, pd.DataFrame(new_payments)], ignore_index=True)
    payments.to_csv(payments_file, index=False)

def save_cost(apartment, location, cost_type, amount, description, receipt_img=None):
    costs = pd.read_csv(costs_file)
    receipt_path = ""
    if receipt_img is not None:
        receipt_filename = f"cost_{apartment}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        receipt_path = os.path.join(receipts_folder, receipt_filename)
        with open(receipt_path, "wb") as f:
            f.write(receipt_img.getbuffer())
    new_cost = pd.DataFrame([{
        "Apartment": apartment,
        "Location": location,
        "Cost Type": cost_type,
        "Amount": amount,
        "Description": description,
        "Date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "Receipt": receipt_path
    }])
    costs = pd.concat([costs, new_cost], ignore_index=True)
    costs.to_csv(costs_file, index=False)

def delete_tenant(tenant_id):
    tenants = pd.read_csv(tenants_file)
    tenants = tenants[tenants["Tenant ID"] != tenant_id]
    tenants.to_csv(tenants_file, index=False)
    payments = pd.read_csv(payments_file)
    payments = payments[payments["Tenant ID"] != tenant_id]
    payments.to_csv(payments_file, index=False)

def delete_payment(payment_index):
    payments = pd.read_csv(payments_file)
    receipt_path = payments.loc[payment_index, "Receipt"]
    if pd.notna(receipt_path) and os.path.exists(receipt_path):
        os.remove(receipt_path)
    payments.drop(index=payment_index, inplace=True)
    payments.to_csv(payments_file, index=False)

def delete_cost(cost_index):
    costs = pd.read_csv(costs_file)
    costs.drop(index=cost_index, inplace=True)
    costs.to_csv(costs_file, index=False)

def get_due_months(tenant_id, registration_date, rent_amount=100):
    current_month = datetime.datetime.now().strftime("%Y-%m")
    date_range = pd.date_range(start=registration_date, end=current_month, freq='MS').strftime("%Y-%m")
    payments = pd.read_csv(payments_file)
    paid_months = payments[payments["Tenant ID"] == tenant_id]["Month"].unique()
    due_months = [m for m in date_range if m not in paid_months]
    total_due = len(due_months) * rent_amount
    return due_months, total_due, paid_months

def get_total_paid(tenant_id):
    payments = pd.read_csv(payments_file)
    return payments[payments["Tenant ID"] == tenant_id]["Amount"].sum()

# --- Streamlit App ---
st.set_page_config(page_title="Tenants Manager", layout="wide")
with st.sidebar:
    st.title("🏠 Tenants Manager")
    menu = ["Register Tenant", "Record Payment", "Record Cost", "Payment Status", "All Tenants", "Reports & Charts"]
    choice = st.selectbox("Navigation", menu)

st.title("📋 Nkem-Njinju Tenants Management System")

# Pages
if choice == "Register Tenant":
    st.subheader("📅 Register a New Tenant")
    tenant_id = st.text_input("Tenant ID")
    name = st.text_input("Full Name")
    apartment = st.text_input("Apartment")
    phone = st.text_input("Phone Number")
    location = st.selectbox("Location", ["Checkpoint", "Sossoliso", "Molyko"])

    if st.button("Register Tenant"):
        if tenant_id and name and apartment:
            save_tenant(tenant_id, name, apartment, phone, location)
            st.success(f"✅ Tenant {name} registered successfully.")
        else:
            st.warning("⚠️ Please fill in all required fields.")

elif choice == "Record Payment":
    st.subheader("💳 Record a Payment")
    tenants, payments, _ = load_data()
    tenant_ids = tenants["Tenant ID"].tolist()
    selected_id = st.selectbox("Select Tenant ID", tenant_ids)

    if selected_id:
        paid_months = payments[payments["Tenant ID"] == selected_id]["Month"].tolist()
        if paid_months:
            st.info(f"🗓️ Already paid for: {', '.join(paid_months)}")
        else:
            st.info("🗓️ No previous payments recorded.")

    month = st.text_input("Start Month Paying For (YYYY-MM)", value=datetime.datetime.now().strftime("%Y-%m"))
    num_months = st.number_input("Number of Months Paid For", min_value=1, max_value=12, value=1)
    amount_per_month = st.number_input("Amount Paid per Month", min_value=0.0)
    location = st.selectbox("Location", ["Checkpoint", "Sossoliso", "Molyko"])
    receipt = st.file_uploader("Upload Receipt Image", type=["png", "jpg", "jpeg"])

    if receipt:
        st.image(receipt, width=100, caption="Receipt Preview")

    if st.button("Save Payment"):
        save_payment(selected_id, month, num_months, amount_per_month, receipt, location)
        st.success("✅ Payment recorded successfully.")

elif choice == "Record Cost":
    st.subheader("🛠️ Record an Apartment Cost")
    _, _, _ = load_data()
    apartment = st.text_input("Apartment")
    location = st.selectbox("Location", ["Checkpoint", "Sossoliso", "Molyko"])
    cost_type = st.selectbox("Cost Type", ["Water", "Light", "Repair", "Other"])
    amount = st.number_input("Cost Amount", min_value=0.0)
    description = st.text_area("Description")
    receipt = st.file_uploader("Upload Cost Receipt (optional)", type=["png", "jpg", "jpeg"])

    if receipt:
        st.image(receipt, width=100, caption="Receipt Preview")

    if st.button("Save Cost"):
        if apartment and amount > 0:
            save_cost(apartment, location, cost_type, amount, description, receipt)
            st.success("✅ Cost recorded successfully.")
        else:
            st.warning("⚠️ Please fill in the apartment and cost amount.")

elif choice == "Payment Status":
    st.subheader("📊 Payment Status Overview")
    tenants, payments, _ = load_data()
    rent_amount = st.number_input("Monthly Rent Amount (default: 50,000)", value=50000)
    search_term = st.text_input("🔍 Search by Name, Apartment, or Phone")

    if search_term:
        tenants = tenants[tenants.apply(lambda row: search_term.lower() in row.to_string().lower(), axis=1)]

    for _, row in tenants.iterrows():
        registration_month = row.get("Registration Date", datetime.datetime.now().strftime("%Y-%m"))
        due_months, total_due, paid_months = get_due_months(row["Tenant ID"], registration_month, rent_amount)
        total_paid = get_total_paid(row["Tenant ID"])

        # Color indicator
        if len(due_months) <= 1:
            status_icon = "✅"
        elif len(due_months) <= 2:
            status_icon = "⚠️"
        else:
            status_icon = "❌"

        with st.expander(f"{status_icon} {row['Name']} - Apartment {row['Apartment']}"):
            st.markdown(f"**Phone:** {row['Phone']}")
            st.markdown(f"**Location:** {row['Location']}")
            st.markdown(f"**Total Paid:** {total_paid} FCFA")
            st.markdown(f"**Total Due:** {total_due} FCFA")
            st.markdown(f"**Due Months:** {', '.join(due_months)}")
            st.markdown(f"**Paid Months:** {', '.join(paid_months)}")

elif choice == "All Tenants":
    st.subheader("📋 List of All Tenants")
    tenants, _, _ = load_data()
    for idx, row in tenants.iterrows():
        total_paid = get_total_paid(row["Tenant ID"])
        with st.expander(f"{row['Name']} - Apartment {row['Apartment']}"):
            st.markdown(f"**Tenant ID:** {row['Tenant ID']}")
            st.markdown(f"**Phone:** {row['Phone']}")
            st.markdown(f"**Location:** {row['Location']}")
            st.markdown(f"**Registered:** {row['Registration Date']}")
            st.markdown(f"**Total Paid:** {total_paid} FCFA")
            st.warning("⚠️ Deleting this tenant will also delete all their payment records.")
            confirm_delete = st.checkbox(f"✅ Confirm delete {row['Name']} and their payments", key=f"confirm_delete_{idx}")
            if confirm_delete:
                if st.button(f"🗑️ Delete {row['Name']}", key=f"delete_{idx}"):
                    delete_tenant(row['Tenant ID'])
                    st.success(f"✅ Tenant {row['Name']} and their payments deleted successfully!")
                    st.experimental_rerun()

elif choice == "Reports & Charts":
    st.subheader("📊 Reports & Charts")
    _, payments, costs = load_data()

    if not payments.empty:
        st.markdown("### 💳 Payment Analysis by Location")
        payment_summary_location = payments.groupby("Location").agg({"Amount": "sum"}).reset_index()
        st.dataframe(payment_summary_location)
        fig = px.bar(payment_summary_location, x="Location", y="Amount", title="Total Payments by Location")
        st.plotly_chart(fig)

    if not costs.empty:
        st.markdown("### 🛠️ Cost Analysis by Location")
        cost_summary_location = costs.groupby("Location").agg({"Amount": "sum"}).reset_index()
        st.dataframe(cost_summary_location)
        fig = px.bar(cost_summary_location, x="Location", y="Amount", title="Total Costs by Location")
        st.plotly_chart(fig)

        st.subheader("📸 View Cost Receipts by Location")
        for location in costs["Location"].unique():
            location_costs = costs[costs["Location"] == location]
            with st.expander(f"Costs for Location: {location}"):
                for idx, row in location_costs.iterrows():
                    st.markdown(f"**Apartment:** {row['Apartment']} - **Cost Type:** {row['Cost Type']} ({row['Amount']} FCFA)")
                    st.markdown(f"**Description:** {row['Description']}")
                    st.markdown(f"**Date:** {row['Date']}")
                    if 'Receipt' in row and pd.notna(row['Receipt']) and os.path.exists(row['Receipt']):
                        st.image(row['Receipt'], width=300)

                    confirm_delete = st.checkbox(f"✅ Confirm delete Cost ID {idx}", key=f"confirm_cost_{idx}")
                    if confirm_delete:
                        if st.button(f"🗑️ Delete Cost ID {idx}", key=f"delete_cost_{idx}"):
                            delete_cost(idx)
                            st.success(f"✅ Deleted cost record {idx} successfully!")
                            st.experimental_rerun()
