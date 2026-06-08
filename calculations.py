# calculations.py
import math

def calculate_total_load(appliances):
    """
    Formula 1: P_total = Sum(P_i)
    appliances: List of dicts, e.g., [{'power': 60, 'quantity': 2}]
    """
    return sum(app['power'] * app.get('quantity', 1) for app in appliances)

def calculate_daily_consumption(appliances):
    """
    Formula 2: Ed = Sum(P_i * t_i)
    Returns daily energy demand in Wh/day.
    """
    return sum(app['power'] * app['hours'] * app.get('quantity', 1) for app in appliances)

def calculate_corrected_energy(E_d, efficiency=0.85):
    """
    Formula 3: Ec = Ed / η
    η = system efficiency (typically 0.8 to 0.85)
    """
    return E_d / efficiency

def size_solar_pv(E_c, peak_sun_hours=5.0):
    """
    Formula 4: Ppv = Ec / Hs
    Hs = peak sun hours (typically 4 to 6 hours in Nigeria)
    """
    return E_c / peak_sun_hours

def size_number_of_panels(P_pv, P_panel):
    """
    Formula 5: Np = Ppv / Ppanel
    """
    return math.ceil(P_pv / P_panel) if P_panel > 0 else 0

def size_battery_capacity(E_d, days_of_autonomy, battery_voltage, dod):
    """
    Formula 6: Cb = (Ed * Da) / (Vb * DOD)
    dod: depth of discharge (Lead Acid = 0.5, Lithium = 0.8)
    """
    denom = battery_voltage * dod
    if denom == 0:
        return 0
    return (E_d * days_of_autonomy) / denom

def size_number_of_batteries(C_b, C_battery):
    """
    Formula 7: Nb = Cb / Cbattery
    """
    return math.ceil(C_b / C_battery) if C_battery > 0 else 0

def size_inverter(P_total, safety_factor=1.25):
    """
    Formula 8: Pinv = Ptotal * SF
    """
    return P_total * safety_factor

def size_charge_controller_current(P_pv, system_voltage, safety_factor=1.25):
    """
    Formula 9: Ic = Ppv / Vs
    Apply safety factor: I_controller = Ic * 1.25
    """
    if system_voltage == 0:
        return 0
    I_c = P_pv / system_voltage
    return I_c * safety_factor

def calculate_panel_efficiency(P_out, P_in):
    """
    Formula 10: η = (Pout / Pin) * 100
    """
    return (P_out / P_in) * 100 if P_in > 0 else 0

def calculate_battery_energy(voltage, ah_rating):
    """
    Formula 11: Eb = V * Ah
    """
    return voltage * ah_rating

def calculate_solar_irradiance_power(area, efficiency, irradiance, performance_ratio=0.75):
    """
    Formula 12: P = A * r * H * PR
    """
    return area * efficiency * irradiance * performance_ratio