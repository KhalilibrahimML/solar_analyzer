import streamlit as st
import pandas as pd
import random
import json
import os
from datetime import datetime
from urllib import error, request

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

with st.sidebar.expander("Gemini AI", expanded=False):
    st.text_input(
        "GEMINI_API_KEY",
        type="password",
        key="gemini_api_key",
        help="Paste your Gemini API key here if it is not already set in your environment or Streamlit secrets.",
    )
    st.caption("Stored only in the current Streamlit session.")

# Load project data
appliances = db.get_all_appliances()
logs = db.get_generation_logs()

DEFAULT_SYSTEM_SETTINGS = {
    "system_voltage": 24.0,
    "peak_sun_hours": 5.0,
    "depth_of_discharge": 0.8,
    "panel_wattage": 350.0,
    "battery_voltage": 24.0,
    "battery_unit_capacity_ah": 200.0,
    "days_of_autonomy": 1.5,
    "system_efficiency": 0.85,
}


def ensure_session_defaults():
    for key, value in DEFAULT_SYSTEM_SETTINGS.items():
        st.session_state.setdefault(key, value)
    st.session_state.setdefault("ai_optimization_report", "")
    st.session_state.setdefault("ai_optimization_error", "")
    st.session_state.setdefault("gemini_api_key", os.getenv("GEMINI_API_KEY", ""))


def get_system_settings():
    return {key: st.session_state[key] for key in DEFAULT_SYSTEM_SETTINGS}


def build_live_sizing_profile(appliance_rows, system_settings):
    total_load = calc.calculate_total_load(appliance_rows) if appliance_rows else 0
    daily_consumption = (
        calc.calculate_daily_consumption(appliance_rows) if appliance_rows else 0
    )
    corrected_energy = (
        calc.calculate_corrected_energy(
            daily_consumption, system_settings["system_efficiency"]
        )
        if daily_consumption
        else 0
    )
    pv_power = (
        calc.size_solar_pv(corrected_energy, system_settings["peak_sun_hours"])
        if corrected_energy
        else 0
    )
    n_panels = calc.size_number_of_panels(pv_power, system_settings["panel_wattage"])
    battery_capacity = calc.size_battery_capacity(
        daily_consumption,
        system_settings["days_of_autonomy"],
        system_settings["battery_voltage"],
        system_settings["depth_of_discharge"],
    )
    n_batteries = calc.size_number_of_batteries(
        battery_capacity, system_settings["battery_unit_capacity_ah"]
    )
    inverter_power = calc.size_inverter(total_load, safety_factor=1.25)
    charge_current = calc.size_charge_controller_current(
        pv_power, system_settings["system_voltage"]
    )

    average_hourly_demand = daily_consumption / 24 if daily_consumption else 0
    profile_rows = []
    for hour in range(24):
        if 6 <= hour <= 18:
            sunlight_shape = max(0.0, 1 - abs(hour - 12) / 6)
            solar_supply = (
                pv_power * sunlight_shape * system_settings["system_efficiency"]
            )
        else:
            solar_supply = 0.0

        profile_rows.append(
            {
                "hour": hour,
                "solar_supply_wh": round(solar_supply, 2),
                "constant_demand_wh": round(average_hourly_demand, 2),
            }
        )

    profile_frame = pd.DataFrame(profile_rows)
    return {
        "total_load": total_load,
        "daily_consumption": daily_consumption,
        "corrected_energy": corrected_energy,
        "pv_power": pv_power,
        "n_panels": n_panels,
        "battery_capacity": battery_capacity,
        "n_batteries": n_batteries,
        "inverter_power": inverter_power,
        "charge_current": charge_current,
        "profile_frame": profile_frame,
    }


def build_optimization_prompt(appliance_rows, system_settings, profile):
    appliance_lines = [
        f"- {row['name']}: {row['power']} W, {row['quantity']} units, {row['hours']} h/day"
        for row in appliance_rows
    ]
    if not appliance_lines:
        appliance_lines = ["- No appliances configured yet."]

    return (
        "You are a senior solar PV system designer. Review this configuration and give "
        "component optimization tips, sizing risks, and maintenance advice. Keep the reply "
        "practical, specific, and concise.\n\n"
        f"System voltage: {system_settings['system_voltage']} V\n"
        f"Peak sun hours: {system_settings['peak_sun_hours']} h\n"
        f"Depth of discharge: {system_settings['depth_of_discharge'] * 100:.0f}%\n"
        f"Panel wattage: {system_settings['panel_wattage']} W\n"
        f"Battery voltage: {system_settings['battery_voltage']} V\n"
        f"Battery unit capacity: {system_settings['battery_unit_capacity_ah']} Ah\n"
        f"Days of autonomy: {system_settings['days_of_autonomy']}\n"
        f"System efficiency: {system_settings['system_efficiency'] * 100:.0f}%\n\n"
        f"Sizing results:\n"
        f"- Total load: {profile['total_load']:.0f} W\n"
        f"- Daily consumption: {profile['daily_consumption'] / 1000:.2f} kWh\n"
        f"- Corrected energy: {profile['corrected_energy'] / 1000:.2f} kWh\n"
        f"- PV power: {profile['pv_power']:.0f} W\n"
        f"- Panels required: {profile['n_panels']}\n"
        f"- Battery capacity: {profile['battery_capacity']:.0f} Ah\n"
        f"- Batteries required: {profile['n_batteries']}\n"
        f"- Inverter size: {profile['inverter_power']:.0f} W\n"
        f"- Controller current: {profile['charge_current']:.1f} A\n\n"
        "Appliances:\n"
        + "\n".join(appliance_lines)
        + "\n\nUse the energy profile shape below as context for supply versus demand:\n"
        + profile["profile_frame"].to_string(index=False)
    )


def get_gemini_api_key():
    if st.session_state.get("gemini_api_key"):
        return st.session_state.get("gemini_api_key")

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key

    try:
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


def analyze_with_gemini(prompt_text):
    api_key = get_gemini_api_key()
    if not api_key:
        return (
            None,
            "Set GEMINI_API_KEY in your environment or Streamlit secrets to enable AI optimization.",
        )

    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"temperature": 0.35, "maxOutputTokens": 700},
    }
    body = json.dumps(payload).encode("utf-8")
    api_request = request.Request(
        endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )

    try:
        with request.urlopen(api_request, timeout=30) as response:
            raw_response = response.read().decode("utf-8")
        response_json = json.loads(raw_response)
        return (
            response_json["candidates"][0]["content"]["parts"][0]["text"],
            None,
        )
    except error.HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="ignore") if exc.fp else str(exc)
        return None, f"Gemini request failed: {error_text or exc}"
    except Exception as exc:
        return None, f"Gemini request failed: {exc}"


def save_appliance_edits(edited_appliances):
    validation_errors = []
    for _, row in edited_appliances.iterrows():
        appliance_name = str(row["name"]).strip()
        if not appliance_name:
            validation_errors.append("Each appliance needs a name before saving.")
            continue

        db.update_appliance(
            int(row["id"]),
            appliance_name,
            float(row["power"]),
            float(row["hours"]),
            int(round(row["quantity"])),
        )

    return validation_errors


ensure_session_defaults()
system_settings = get_system_settings()
live_profile = build_live_sizing_profile(appliances, system_settings)


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

if "pending_delete_appliance_id" not in st.session_state:
    st.session_state.pending_delete_appliance_id = None
    st.session_state.pending_delete_appliance_name = ""

if "pending_delete_log_date" not in st.session_state:
    st.session_state.pending_delete_log_date = None


if page == "Dashboard":
    st.subheader("Dashboard Overview")
    st.caption(
        "Adjust appliances or system constants on Load Management to refresh these results instantly."
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Load", f"{live_profile['total_load']:.0f} W")
    col2.metric(
        "Daily Consumption", f"{live_profile['daily_consumption'] / 1000:.2f} kWh"
    )
    col3.metric(
        "Corrected Energy", f"{live_profile['corrected_energy'] / 1000:.2f} kWh"
    )
    col4.metric(
        "System Efficiency", f"{system_settings['system_efficiency'] * 100:.0f}%"
    )

    st.markdown("---")
    st.subheader("Live Sizing Snapshot")
    sizing_cols = st.columns(4)
    sizing_cols[0].metric("Panels Required", f"{live_profile['n_panels']}")
    sizing_cols[1].metric("Batteries Required", f"{live_profile['n_batteries']}")
    sizing_cols[2].metric("PV Array Size", f"{live_profile['pv_power']:.0f} W")
    sizing_cols[3].metric(
        "Controller Current", f"{live_profile['charge_current']:.1f} A"
    )

    st.markdown("---")
    st.subheader("Energy Profile Chart")
    st.line_chart(
        live_profile["profile_frame"].set_index("hour")[
            ["solar_supply_wh", "constant_demand_wh"]
        ]
    )

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
        total_load = live_profile["total_load"]
        daily_consumption = live_profile["daily_consumption"]
        corrected_energy = live_profile["corrected_energy"]
        pv_power = live_profile["pv_power"]
        n_panels = live_profile["n_panels"]
        battery_capacity = live_profile["battery_capacity"]
        n_batteries = live_profile["n_batteries"]
        inverter_power = live_profile["inverter_power"]
        charge_current = live_profile["charge_current"]

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
        st.markdown("---")
        st.subheader("Energy Profile Chart")
        st.line_chart(
            live_profile["profile_frame"].set_index("hour")[
                ["solar_supply_wh", "constant_demand_wh"]
            ]
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
            st.rerun()

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
    st.write(
        "Add appliances, edit their ratings, and tune system constants to recalculate sizing live."
    )

    st.markdown("### System Parameters")
    system_col1, system_col2, system_col3, system_col4 = st.columns(4)
    with system_col1:
        st.number_input(
            "System Voltage (V)",
            min_value=12.0,
            step=12.0,
            key="system_voltage",
        )
        st.number_input(
            "Peak Sun Hours",
            min_value=1.0,
            step=0.1,
            format="%.1f",
            key="peak_sun_hours",
        )
    with system_col2:
        st.number_input(
            "Depth of Discharge",
            min_value=0.1,
            max_value=1.0,
            step=0.05,
            format="%.2f",
            key="depth_of_discharge",
        )
        st.number_input(
            "System Efficiency",
            min_value=0.1,
            max_value=1.0,
            step=0.01,
            format="%.2f",
            key="system_efficiency",
        )
    with system_col3:
        st.number_input(
            "Panel Wattage (W)",
            min_value=1.0,
            step=10.0,
            format="%.0f",
            key="panel_wattage",
        )
        st.number_input(
            "Battery Voltage (V)",
            min_value=1.0,
            step=12.0,
            format="%.0f",
            key="battery_voltage",
        )
    with system_col4:
        st.number_input(
            "Battery Unit Capacity (Ah)",
            min_value=1.0,
            step=10.0,
            format="%.0f",
            key="battery_unit_capacity_ah",
        )
        st.number_input(
            "Days of Autonomy",
            min_value=0.5,
            step=0.5,
            format="%.1f",
            key="days_of_autonomy",
        )

    st.caption(
        "These values are shared across the dashboard, system analysis, and AI optimization prompt."
    )

    with st.expander("Add New Appliance", expanded=True):
        name = st.text_input("Appliance Name")
        power = st.number_input("Power (W)", min_value=1.0, step=1.0, format="%.1f")
        hours = st.number_input("Hours per Day", min_value=0.1, step=0.1, format="%.1f")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        if st.button("Add Appliance"):
            if name.strip():
                db.add_appliance(name.strip(), power, hours, quantity)
                st.success(f"Added {name.strip()}.")
                st.rerun()
            else:
                st.error("Please enter an appliance name.")

    if appliances:
        st.markdown("### Current Appliances")
        appliance_frame = pd.DataFrame(appliances)[
            ["id", "name", "power", "hours", "quantity"]
        ]
        edited_appliances = st.data_editor(
            appliance_frame,
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "name": st.column_config.TextColumn("Appliance"),
                "power": st.column_config.NumberColumn(
                    "Power (W)", min_value=1.0, step=1.0
                ),
                "hours": st.column_config.NumberColumn(
                    "Hours/Day", min_value=0.1, step=0.1
                ),
                "quantity": st.column_config.NumberColumn("Qty", min_value=1, step=1),
            },
            disabled=["id"],
        )

        edit_col1, edit_col2 = st.columns([1, 3])
        if edit_col1.button("Save Appliance Changes"):
            validation_errors = save_appliance_edits(edited_appliances)
            if validation_errors:
                st.error(validation_errors[0])
            else:
                st.success("Appliance changes saved.")
                st.rerun()

        st.markdown("### Delete Appliances")
        header_cols = st.columns([3, 1, 1, 1, 1, 1])
        header_cols[0].write("**Appliance**")
        header_cols[1].write("**Power (W)**")
        header_cols[2].write("**Hours/Day**")
        header_cols[3].write("**Qty**")
        header_cols[4].write("**Daily (Wh)**")
        header_cols[5].write("**Action**")

        for app in appliances:
            daily_wh = app["power"] * app["hours"] * app["quantity"]
            row_cols = st.columns([3, 1, 1, 1, 1, 1])
            row_cols[0].write(app["name"])
            row_cols[1].write(f"{app['power']:.1f}")
            row_cols[2].write(f"{app['hours']:.1f}")
            row_cols[3].write(app["quantity"])
            row_cols[4].write(f"{daily_wh:.0f}")
            if row_cols[5].button("Delete", key=f"delete_app_{app['id']}"):
                st.session_state.pending_delete_appliance_id = app["id"]
                st.session_state.pending_delete_appliance_name = app["name"]
                st.rerun()

        if st.session_state.pending_delete_appliance_id:
            st.warning(
                f"Confirm deletion of '{st.session_state.pending_delete_appliance_name}'? This cannot be undone."
            )
            confirm_cols = st.columns([1, 1])
            if confirm_cols[0].button("Confirm Delete Appliance"):
                db.delete_appliance(st.session_state.pending_delete_appliance_id)
                st.success(f"Deleted {st.session_state.pending_delete_appliance_name}.")
                st.session_state.pending_delete_appliance_id = None
                st.session_state.pending_delete_appliance_name = ""
                st.rerun()
            if confirm_cols[1].button("Cancel"):
                st.session_state.pending_delete_appliance_id = None
                st.session_state.pending_delete_appliance_name = ""
                st.rerun()

        st.markdown("---")
        if st.button("Delete All Appliances", type="secondary"):
            st.session_state.pending_delete_appliance_id = -1
            st.session_state.pending_delete_appliance_name = "all appliances"
            st.rerun()

        if st.session_state.pending_delete_appliance_id == -1:
            st.warning("Confirm deletion of ALL appliances? This cannot be undone.")
            delete_all_cols = st.columns([1, 1])
            if delete_all_cols[0].button("Confirm Delete All Appliances"):
                db.delete_all_appliances()
                st.success("Deleted all appliances.")
                st.session_state.pending_delete_appliance_id = None
                st.session_state.pending_delete_appliance_name = ""
                st.rerun()
            if delete_all_cols[1].button("Cancel", key="cancel_delete_all_appliances"):
                st.session_state.pending_delete_appliance_id = None
                st.session_state.pending_delete_appliance_name = ""
                st.rerun()
    else:
        st.info("No appliance entries yet.")

    st.markdown("---")
    st.subheader("Live Sizing Results")
    result_cols = st.columns(4)
    result_cols[0].metric("Total Load", f"{live_profile['total_load']:.0f} W")
    result_cols[1].metric(
        "Daily Consumption", f"{live_profile['daily_consumption'] / 1000:.2f} kWh"
    )
    result_cols[2].metric("Panels Required", f"{live_profile['n_panels']}")
    result_cols[3].metric("Batteries Required", f"{live_profile['n_batteries']}")

    result_cols = st.columns(4)
    result_cols[0].metric("PV Array Size", f"{live_profile['pv_power']:.0f} W")
    result_cols[1].metric(
        "Battery Capacity", f"{live_profile['battery_capacity']:.0f} Ah"
    )
    result_cols[2].metric("Inverter Size", f"{live_profile['inverter_power']:.0f} W")
    result_cols[3].metric(
        "Controller Current", f"{live_profile['charge_current']:.1f} A"
    )

    st.markdown("### Energy Profile Chart")
    st.line_chart(
        live_profile["profile_frame"].set_index("hour")[
            ["solar_supply_wh", "constant_demand_wh"]
        ]
    )

    st.markdown("### AI Optimization")
    st.write(
        "Send the current configuration to Gemini for component optimization tips and maintenance advice."
    )
    prompt_text = build_optimization_prompt(appliances, system_settings, live_profile)
    if st.button("Analyze with AI"):
        report_text, report_error = analyze_with_gemini(prompt_text)
        st.session_state.ai_optimization_report = report_text or ""
        st.session_state.ai_optimization_error = report_error or ""

    if st.session_state.ai_optimization_error:
        st.error(st.session_state.ai_optimization_error)

    if st.session_state.ai_optimization_report:
        st.markdown(st.session_state.ai_optimization_report)

elif page == "Reports":
    st.subheader("Historical Reports")
    with st.expander("Add New Generation Log"):
        log_date = st.date_input("Date")
        irradiance = st.number_input(
            "Irradiance (kWh/m²)", min_value=0.0, step=0.1, format="%.2f"
        )
        generation = st.number_input(
            "Generation (kWh)", min_value=0.0, step=0.1, format="%.2f"
        )
        load = st.number_input(
            "Load Consumed (kWh)", min_value=0.0, step=0.1, format="%.2f"
        )
        if st.button("Save Log"):
            db.add_generation_log(
                log_date.strftime("%Y-%m-%d"), irradiance, generation, load
            )
            st.success("Generation log added.")
            st.rerun()

    if logs:
        df_logs = pd.DataFrame(
            logs, columns=["date", "irradiance", "generation", "load"]
        )
        df_logs = df_logs.rename(
            columns={"generation": "actual_generation_kwh", "load": "load_consumed_kwh"}
        )
        st.table(df_logs)

        st.markdown("### Delete Log Entry")
        for log in logs:
            delete_cols = st.columns([3, 1, 1, 1, 1])
            delete_cols[0].write(log[0])
            delete_cols[1].write(f"{log[1]:.2f}")
            delete_cols[2].write(f"{log[2]:.2f}")
            delete_cols[3].write(f"{log[3]:.2f}")
            if delete_cols[4].button("Delete", key=f"delete_log_{log[0]}"):
                st.session_state.pending_delete_log_date = log[0]
                st.rerun()

        st.markdown("---")
        if st.button("Delete All Logs", type="secondary"):
            st.session_state.pending_delete_log_date = "ALL"
            st.rerun()

        if st.session_state.pending_delete_log_date:
            if st.session_state.pending_delete_log_date == "ALL":
                st.warning(
                    "Confirm deletion of ALL generation logs? This action cannot be undone."
                )
                log_confirm_cols = st.columns([1, 1])
                if log_confirm_cols[0].button("Confirm Delete All Logs"):
                    db.delete_all_generation_logs()
                    st.success("Deleted all logs.")
                    st.session_state.pending_delete_log_date = None
                    st.rerun()
                if log_confirm_cols[1].button("Cancel", key="cancel_delete_all_logs"):
                    st.session_state.pending_delete_log_date = None
                    st.rerun()
            else:
                st.warning(
                    f"Delete generation log for {st.session_state.pending_delete_log_date}? This action cannot be undone."
                )
                log_confirm_cols = st.columns([1, 1])
                if log_confirm_cols[0].button("Confirm Delete Log"):
                    db.delete_generation_log(st.session_state.pending_delete_log_date)
                    st.success(
                        f"Deleted log {st.session_state.pending_delete_log_date}."
                    )
                    st.session_state.pending_delete_log_date = None
                    st.rerun()
                if log_confirm_cols[1].button("Cancel", key="cancel_delete_log"):
                    st.session_state.pending_delete_log_date = None
                    st.rerun()

        st.line_chart(
            df_logs.set_index("date")[["actual_generation_kwh", "load_consumed_kwh"]]
        )
    else:
        st.info("No historical logs available.")
st.sidebar.markdown("---")
st.sidebar.write("Built with Streamlit and your existing solar analyzer modules.")
