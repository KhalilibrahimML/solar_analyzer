# main.py
import calculations as calc
import database as db
import recommendations as rec

def main():
    print("=========================================================================")
    print("  PHOTOVOLTAIC COMPONENT ANALYZER & PERFORMANCE TRACKER WORKBENCH")
    print("=========================================================================\n")
    
    # Initialize Local Database Setup
    db.init_db()
    
    # Auto-seed standard household appliance profile elements if completely clean run
    appliances = db.get_all_appliances()
    if not appliances:
        print("[*] Initializing baseline test load models into SQLite storage...")
        db.add_appliance("Refrigeration Module", power=160, hours=24, quantity=1)
        db.add_appliance("LED Luminaire Array", power=15, hours=8, quantity=8)
        db.add_appliance("Cooling Ventilation Fans", power=60, hours=12, quantity=3)
        db.add_appliance("Computing Node Network", power=90, hours=6, quantity=2)
        appliances = db.get_all_appliances()

    # Section 1: Display Loads
    print("--- 1. CURRENT DEMAND LOAD INVENTORY PROFILES ---")
    for app in appliances:
        print(f" • {app['name']}: {app['power']}W × {app['hours']} hrs/day (Qty: {app['quantity']})")
        
    # Section 2: Execute Equations Engine Workflow
    p_total = calc.calculate_total_load(appliances)
    e_d = calc.calculate_daily_consumption(appliances)
    e_c = calc.calculate_corrected_energy(e_d, efficiency=0.85)
    
    # Static Parameter assumptions for standard environmental deployment context
    p_sun_hours = 5.0     # Average peak sun hours in Northern Nigeria region
    target_module = 350    # 350W individual solar panel rating
    system_vdc = 24       # 24V Operational Configuration
    target_batt_ah = 200  # 200Ah battery cells
    battery_chemistry = "Lithium"
    dod_factor = 0.8 if battery_chemistry == "Lithium" else 0.5
    autonomy_span = 1.5   # 1.5 Days of autonomy reserve design
    
    p_pv = calc.size_solar_pv(e_c, peak_sun_hours=p_sun_hours)
    n_p = calc.size_number_of_panels(p_pv, target_module)
    c_b = calc.size_battery_capacity(e_d, autonomy_span, system_vdc, dod_factor)
    n_b = calc.size_number_of_batteries(c_b, target_batt_ah)
    p_inv = calc.size_inverter(p_total, safety_factor=1.25)
    i_cc = calc.size_charge_controller_current(p_pv, system_voltage=system_vdc)
    
    print("\n--- 2. TRANSLATED PHOTOVOLTAIC ENGINEERING COMPONENT SIZING SIZING ---")
    print(f" • Total Peak Dynamic Demand  : {p_total:.2f} W")
    print(f" • Calculated Daily Energy    : {e_d:.2f} Wh/day")
    print(f" • Corrected Operational Load : {e_c:.2f} Wh/day (Adjusted at 85% efficiency baseline)")
    print(f" • Minimum PV Array Capacity  : {p_pv:.2f} W required")
    print(f" • Recommended Solar Panels   : {n_p} Modules ({target_module}W array elements)")
    print(f" • Target Battery Capacity    : {c_b:.2f} Ah (Configured at {system_vdc}V bus)")
    print(f" • Total Battery Pack Quantities: {n_b} Packs ({target_batt_ah}Ah units)")
    print(f" • Minimum Inverter Sizing     : {p_inv:.2f} W rated (1.25 Safety threshold)")
    print(f" • Solar Controller Ampacity   : {i_cc:.2f} A minimum safety current")
    
    # Section 3: Engineering Sizing Advisory Insights
    print("\n--- 3. SYSTEM SCHEMATIC ARTIFACT RECOMMENDATIONS ---")
    sizing_summary = {'inverter_w': p_inv}
    advisory_recs = rec.get_sizing_recommendations(sizing_summary, battery_chemistry)
    for advice in advisory_recs:
        print(f"  [Advisory] {advice}")
        
    # Section 4: Data-Driven Performance Monitoring & Anomalies Diagnostic Execution
    print("\n--- 4. DATA-DRIVEN HISTORICAL DIAGNOSTICS & SYSTEM MONITORING ---")
    print(f"{'Log Date':<12} | {'Irradiance Index':<16} | {'Actual Gen (kWh)':<16} | {'Load Draw (kWh)':<15} | {'Health Status'}")
    print("-" * 88)
    
    history_logs = db.get_generation_logs()
    for entry in history_logs:
        health, diagnosis_alerts = rec.generate_system_insights(entry)
        print(f"{entry[0]:<12} | {entry[1]:<16.2f} | {entry[2]:<16.2f} | {entry[3]:<15.2f} | {health}")
        for alert in diagnosis_alerts:
            if health != "Optimal":
                print(f"   └── ⚠️ [ALERT MONITOR]: {alert}")

if __name__ == '__main__':
    main()