import streamlit as st
import pandas as pd
import random
from datetime import datetime

import calculations as calc
import database as db
import recommendations as rec

# Initialize database and seed baseline data
db.init_db()

PAGE_TITLE = "Solar Analyzer Web Dashboard"

st.set_page_config(page_title=PAGE_TITLE, layout="wide")

st.title("☀️ Solar PV Analyzer Web Dashboard")
st.markdown(
    "Use this web dashboard to view load sizing, system analysis, live monitoring, and historical solar performance."
)

# Sidebar navigation
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "System Analysis", "Real-time Monitor", "Load Management", "Reports"],
)

# Load project data
appliances = db.get_all_appliances()
logs = db.get_generation_logs()


def simulate_live_point():
    hour = datetime.now().hour
    if 6 <= hour <= 18:
        base_irradiance = 4.5 + 1.5 * (1 - abs(hour - 12) / 6)
        irradiance = max(0, base_irradiance + random.uniform(-0.4, 0.4))
    else:
        irradiance = 0.0

    generation = irradiance * 8.5 + random.uniform(-0.2, 0.2) if irradiance > 0 else 0.0
    load = max(0.5, 6.5 + random.uniform(-0.5, 0.8))
    efficiency = (generation / (irradiance * 10) * 100) if irradiance > 0 else 0.0
    balance = generation - load

    return {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "irradiance": round(irradiance, 2),
        "generation": round(generation, 2),
        "load": round(load, 2),
        "efficiency": round(efficiency, 1),
        "balance": round(balance, 2),
    }


if "live_data" not in st.session_state:
    st.session_state.live_data = []

if "monitor_active" not in st.session_state:
    st.session_state.monitor_active = False


if page == "Dashboard":
    st.subheader("Dashboard Overview")

    col1, col2, col3, col4 = st.columns(4)

    total_load = calc.calculate_total_load(appliances) if appliances else 0
    daily_consumption = (
        calc.calculate_daily_consumption(appliances) if appliances else 0
    )
    corrected_energy = (
        calc.calculate_corrected_energy(daily_consumption) if appliances else 0
    )
    efficiency = 85

    col1.metric("Total Load", f"{total_load:.0f} W")
    col2.metric("Daily Consumption", f"{daily_consumption / 1000:.2f} kWh")
    col3.metric("Corrected Energy", f"{corrected_energy / 1000:.2f} kWh")
    col4.metric("System Efficiency", f"{efficiency}%")

    st.markdown("---")
    st.subheader("Recent Generation Trend")
    if logs:
        df = pd.DataFrame(logs, columns=["date", "irradiance", "generation", "load"])
        df = df.rename(
            columns={"generation": "actual_generation_kwh", "load": "load_consumed_kwh"}
        )
        chart_data = df.set_index("date")[
            ["actual_generation_kwh", "load_consumed_kwh"]
        ]
        st.line_chart(chart_data)
    else:
        st.info("No generation logs available yet.")

elif page == "System Analysis":
    st.subheader("System Sizing Analysis")

    if appliances:
        col1, col2 = st.columns(2)
        total_load = calc.calculate_total_load(appliances)
        daily_consumption = calc.calculate_daily_consumption(appliances)
        corrected_energy = calc.calculate_corrected_energy(daily_consumption)
        pv_power = calc.size_solar_pv(corrected_energy, peak_sun_hours=5.0)
        n_panels = calc.size_number_of_panels(pv_power, 350)
        battery_capacity = calc.size_battery_capacity(daily_consumption, 1.5, 24, 0.8)
        n_batteries = calc.size_number_of_batteries(battery_capacity, 200)
        inverter_power = calc.size_inverter(total_load, safety_factor=1.25)
        charge_current = calc.size_charge_controller_current(pv_power, 24)

        with col1:
            st.metric("PV Power Required", f"{pv_power:.0f} W")
            st.metric("Number of Panels", f"{n_panels}")
            st.metric("Battery Capacity", f"{battery_capacity:.0f} Ah")

        with col2:
            st.metric("Number of Batteries", f"{n_batteries}")
            st.metric("Inverter Size", f"{inverter_power:.0f} W")
            st.metric("Controller Current", f"{charge_current:.1f} A")

        st.markdown("---")
        st.subheader("Recommendations")
        battery_type = st.selectbox("Battery Chemistry", ["Lithium", "Lead Acid"])
        sizing_info = {
            "inverter_w": inverter_power,
            "battery_capacity_ah": battery_capacity,
        }
        recs = rec.get_sizing_recommendations(sizing_info, battery_type)
        for message in recs:
            st.write(f"- {message}")

        st.markdown("---")
        st.subheader("Appliance Load Breakdown")
        df_appliances = pd.DataFrame(appliances)
        df_appliances["daily_wh"] = (
            df_appliances["power"] * df_appliances["hours"] * df_appliances["quantity"]
        )
        st.dataframe(
            df_appliances[["name", "power", "hours", "quantity", "daily_wh"]].rename(
                columns={
                    "name": "Appliance",
                    "power": "Power (W)",
                    "hours": "Hours/Day",
                    "quantity": "Qty",
                    "daily_wh": "Daily (Wh)",
                }
            )
        )
    else:
        st.warning(
            "No appliances configured. Add appliances on the Load Management page."
        )

elif page == "Real-time Monitor":
    st.subheader("Real-time Monitoring")
    col1, col2 = st.columns([2, 1])

    with col1:
        if st.session_state.monitor_active:
            if st.button("Stop Monitoring"):
                st.session_state.monitor_active = False
        else:
            if st.button("Start Monitoring"):
                st.session_state.monitor_active = True

        if st.session_state.monitor_active:
            st.experimental_rerun()

        if st.session_state.monitor_active:
            point = simulate_live_point()
            st.session_state.live_data.append(point)
            if len(st.session_state.live_data) > 30:
                st.session_state.live_data = st.session_state.live_data[-30:]

        if st.session_state.live_data:
            latest = st.session_state.live_data[-1]
            st.write("### Latest Live Status")
            status_cols = st.columns(3)
            status_cols[0].metric("Irradiance", f"{latest['irradiance']} kWh/m²")
            status_cols[1].metric("Generation", f"{latest['generation']} kWh")
            status_cols[2].metric("Load", f"{latest['load']} kWh")
            status_cols = st.columns(3)
            status_cols[0].metric("Efficiency", f"{latest['efficiency']} %")
            status_cols[1].metric("Balance", f"{latest['balance']} kWh")
            status_cols[2].metric("Timestamp", latest["timestamp"])

            df_live = pd.DataFrame(st.session_state.live_data)
            df_live = df_live.set_index("timestamp")
            st.line_chart(df_live[["irradiance", "generation", "load"]])
            st.line_chart(df_live[["efficiency", "balance"]])

            if latest["balance"] < 0:
                st.error("⚠️ Load exceeds generation. Energy deficit detected.")
            elif latest["efficiency"] < 70:
                st.warning("⚠️ Low efficiency. Check solar panel conditions.")
            else:
                st.success("✅ System operating normally.")
        else:
            st.info("Click Start Monitoring to begin live simulation.")

elif page == "Load Management":
    st.subheader("Load Management")
    st.write("Add appliances to simulate your system load and sizing.")

    with st.expander("Add New Appliance"):
        name = st.text_input("Appliance Name")
        power = st.number_input("Power (W)", min_value=1.0, step=1.0, format="%.1f")
        hours = st.number_input("Hours per Day", min_value=0.1, step=0.1, format="%.1f")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        if st.button("Add Appliance"):
            if name:
                db.add_appliance(name, power, hours, quantity)
                st.success(f"Added {name}.")
                st.experimental_rerun()
            else:
                st.error("Please enter an appliance name.")

    if appliances:
        df_appliances = pd.DataFrame(appliances)
        df_appliances["daily_wh"] = (
            df_appliances["power"] * df_appliances["hours"] * df_appliances["quantity"]
        )
        st.dataframe(
            df_appliances[["name", "power", "hours", "quantity", "daily_wh"]].rename(
                columns={
                    "name": "Appliance",
                    "power": "Power (W)",
                    "hours": "Hours/Day",
                    "quantity": "Qty",
                    "daily_wh": "Daily (Wh)",
                }
            )
        )
    else:
        st.info("No appliance entries yet.")

elif page == "Reports":
    st.subheader("Historical Reports")
    if logs:
        df_logs = pd.DataFrame(
            logs, columns=["date", "irradiance", "generation", "load"]
        )
        df_logs = df_logs.rename(
            columns={"generation": "actual_generation_kwh", "load": "load_consumed_kwh"}
        )
        st.table(df_logs)
        st.line_chart(
            df_logs.set_index("date")[["actual_generation_kwh", "load_consumed_kwh"]]
        )
    else:
        st.info("No historical logs available.")

st.sidebar.markdown("---")
st.sidebar.write("Built with Streamlit and your existing solar analyzer modules.")
