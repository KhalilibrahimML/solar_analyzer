# recommendations.py


def generate_system_insights(actual_log, expected_efficiency=0.85):
    """
    Applies heuristics to classify system health performance profiles.
    """
    date, irradiance, actual_gen, load_consumed = actual_log
    alerts = []
    status = "Optimal"

    # Calculate a baseline reference yield expectation dynamically
    # E.g., Estimating baseline generation thresholds from solar resource exposure parameters
    expected_min_yield = irradiance * 2.8 * expected_efficiency

    if irradiance > 4.0 and actual_gen < expected_min_yield * 0.7:
        status = "Underperforming"
        alerts.append(
            "System optimization needed! Output drops below expected capacity limits. Action: Clear dust accumulation or check panel strings."
        )
    elif actual_gen < load_consumed:
        status = "Deficit Run"
        alerts.append(
            f"Energy balance negative. Consumption ({load_consumed} kWh) outpaced solar yield. Shed secondary appliances to safeguard storage life."
        )
    else:
        alerts.append("System operating efficiently. Stable energy buffer preserved.")

    return status, alerts


def get_sizing_recommendations(sizing_results, battery_type):
    """
    Provides hardware deployment advice based on computed engineering thresholds.
    """
    recs = []
    if battery_type.lower() == "lead acid":
        recs.append(
            "Lead-Acid parameters require well-ventilated housing structures and localized active equalization."
        )
    elif battery_type.lower() == "lithium":
        recs.append(
            "Lithium cells enable deeper depth-of-discharge (80%) thresholds without memory capacity loss degradation."
        )

    if sizing_results.get("inverter_w", 0) > 3000:
        recs.append(
            "High continuous system wattage peak load detected. Upgrade balance-of-system logic to 48V layout parameters to suppress operational line temperatures."
        )
    return recs
