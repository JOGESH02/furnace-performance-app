import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime

st.set_page_config(page_title="FurnaceIQ", page_icon="🔥", layout="wide")

# ---- DATABASE ----
conn = sqlite3.connect("furnace_data.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    operator TEXT,
    scrap_input REAL,
    output REAL,
    scrap_cost REAL,
    selling_price REAL
)
""")
conn.commit()

st.title("🔥 FurnaceIQ")
st.caption("Industrial Recovery & Loss Intelligence System")

menu = st.sidebar.radio("Navigation", ["Add Batch", "Dashboard"])

# =====================
# ADD BATCH
# =====================
if menu == "Add Batch":

    st.subheader("➕ Enter New Batch")

    batch_date = st.date_input("Date", date.today())
    operator = st.text_input("Operator Name")

    scrap_input = st.number_input("Scrap Input (kg)", min_value=0.0)
    output = st.number_input("Output (kg)", min_value=0.0)
    scrap_cost = st.number_input("Scrap Cost (₹/kg)", min_value=0.0)
    selling_price = st.number_input("Selling Price (₹/kg)", min_value=0.0)

    if st.button("Save Batch"):
        c.execute("""
        INSERT INTO batches (date, operator, scrap_input, output, scrap_cost, selling_price)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (str(batch_date), operator, scrap_input, output, scrap_cost, selling_price))
        conn.commit()
        st.success("Batch saved successfully!")

# =====================
# DASHBOARD
# =====================
elif menu == "Dashboard":

    df = pd.read_sql_query("SELECT * FROM batches", conn)

    if df.empty:
        st.info("No data available. Add batches first.")
    else:

        df["date"] = pd.to_datetime(df["date"])

        # ---- DATE FILTER ----
        st.sidebar.subheader("Filter")
        filter_option = st.sidebar.selectbox("Select Period", ["All Time", "This Month"])

        if filter_option == "This Month":
            today = datetime.today()
            df = df[(df["date"].dt.month == today.month) & 
                    (df["date"].dt.year == today.year)]

        if df.empty:
            st.warning("No data for selected period.")
        else:

            # ---- CALCULATIONS ----
            df["recovery %"] = df["output"] / df["scrap_input"]
            df["metal loss (kg)"] = df["scrap_input"] - df["output"]
            df["loss value"] = df["metal loss (kg)"] * df["scrap_cost"]
            df["revenue"] = df["output"] * df["selling_price"]
            df["total scrap cost"] = df["scrap_input"] * df["scrap_cost"]
            df["profit"] = df["revenue"] - df["total scrap cost"]

            avg_recovery = df["recovery %"].mean()
            total_loss_value = df["loss value"].sum()

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Avg Recovery", f"{avg_recovery:.2%}")
            col2.metric("Total Loss (kg)", f"{df['metal loss (kg)'].sum():,.2f}")
            col3.metric("💰 Loss Value (₹)", f"₹{total_loss_value:,.0f}")
            col4.metric("Total Profit (₹)", f"₹{df['profit'].sum():,.0f}")

            st.markdown("---")

            # ---- PERFORMANCE SCORE ----
            score = round(avg_recovery * 100, 1)
            if score >= 97:
                st.success(f"Performance Score: {score}/100 🟢 Excellent")
            elif score >= 93:
                st.warning(f"Performance Score: {score}/100 🟡 Needs Monitoring")
            else:
                st.error(f"Performance Score: {score}/100 🔴 Immediate Attention Required")

            st.markdown("---")

            # ---- RECOVERY TREND ----
            st.subheader("📈 Recovery Trend")
            st.line_chart(df.set_index("date")["recovery %"])

            # ---- WORST BATCH ----
            worst_batch = df.loc[df["recovery %"].idxmin()]
            st.subheader("⚠️ Worst Batch")
            st.write(worst_batch)

            # ---- OPERATOR PERFORMANCE ----
            st.subheader("👷 Operator Ranking")
            operator_stats = df.groupby("operator")["recovery %"].mean().sort_values(ascending=False)
            st.bar_chart(operator_stats)
            st.dataframe(operator_stats)

            st.markdown("---")

            st.subheader("📋 All Batches")
            st.dataframe(df)