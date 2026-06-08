import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import calculations as calc
import database as db
import threading
import time
from datetime import datetime
import random


class SolarAnalyzerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PV Component Analyzer & Monitor")
        self.geometry("1400x800")
        ctk.set_appearance_mode("dark")

        # Initialize database
        db.init_db()

        # Real-time monitoring state
        self.monitoring_active = False
        self.monitor_thread = None
        self.monitor_data = []
        self.monitor_lock = threading.Lock()
        self.update_callbacks = {}  # Store update callbacks for different tabs

        # --- Header ---
        self.header = ctk.CTkFrame(self, height=70, fg_color="#1a1a1a")
        self.header.pack(side="top", fill="x", padx=0, pady=0)

        self.title_label = ctk.CTkLabel(
            self.header,
            text="☀️ Solar PV Analyzer & Monitor",
            font=("Arial", 24, "bold"),
        )
        self.title_label.pack(pady=15, padx=20, anchor="w")

        # --- Tab Navigation ---
        self.tab_frame = ctk.CTkFrame(self, height=50, fg_color="#0d0d0d")
        self.tab_frame.pack(side="top", fill="x", padx=0, pady=0)

        self.tabs = {}
        self.tab_buttons = {}
        self.current_tab = "dashboard"

        tab_names = [
            "Dashboard",
            "System Analysis",
            "Real-time Monitor",
            "Load Management",
            "Reports",
        ]
        tab_keys = ["dashboard", "analysis", "monitor", "loads", "reports"]

        for i, (name, key) in enumerate(zip(tab_names, tab_keys)):
            btn = ctk.CTkButton(
                self.tab_frame,
                text=name,
                width=140,
                height=40,
                command=lambda k=key: self.switch_tab(k),
                fg_color="#2b2b2b",
                hover_color="#3d3d3d",
            )
            btn.pack(side="left", padx=5, pady=8)
            self.tab_buttons[key] = btn

        # --- Content Frame ---
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(
            side="bottom", fill="both", expand=True, padx=10, pady=10
        )

        # Create all tab content
        self.create_dashboard_tab()
        self.create_analysis_tab()
        self.create_monitor_tab()
        self.create_loads_tab()
        self.create_reports_tab()

        # Show initial tab
        self.switch_tab("dashboard")

    def switch_tab(self, tab_name):
        """Switch between tabs"""
        # Hide all tabs
        for tab in self.tabs.values():
            tab.pack_forget()

        # Show selected tab
        self.tabs[tab_name].pack(fill="both", expand=True)
        self.current_tab = tab_name

        # Update button styling
        for key, btn in self.tab_buttons.items():
            if key == tab_name:
                btn.configure(fg_color="#1f538d")
            else:
                btn.configure(fg_color="#2b2b2b")

    def create_kpi_card(self, parent, title, value, unit="", color="#1f538d"):
        """Create a KPI card widget"""
        card = ctk.CTkFrame(parent, fg_color="#1a1a1a", corner_radius=10)

        title_label = ctk.CTkLabel(
            card, text=title, font=("Arial", 12), text_color="#888888"
        )
        title_label.pack(pady=(10, 5), padx=15)

        value_label = ctk.CTkLabel(
            card, text=f"{value} {unit}", font=("Arial", 20, "bold"), text_color=color
        )
        value_label.pack(pady=5, padx=15)

        return card

    def generate_simulated_data(self):
        """Generate realistic simulated solar panel data"""
        # Simulate hourly variations
        hour = datetime.now().hour

        # Solar irradiance varies throughout the day (peak at noon)
        if 6 <= hour <= 18:
            base_irradiance = 4.5 + 1.5 * (1 - abs(hour - 12) / 6)
            irradiance = max(0, base_irradiance + random.uniform(-0.5, 0.5))
        else:
            irradiance = 0

        # Generation proportional to irradiance
        generation = (
            irradiance * 8.5 + random.uniform(-0.2, 0.2) if irradiance > 0 else 0
        )

        # Load consumption is more stable but has some variation
        load = 6.5 + random.uniform(-0.5, 0.8)

        return {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "irradiance": max(0, irradiance),
            "generation": max(0, generation),
            "load": load,
            "efficiency": (generation / (irradiance * 10) * 100)
            if irradiance > 0
            else 0,
            "balance": generation - load,
        }

    def monitor_thread_worker(self):
        """Background thread for collecting real-time data"""
        while self.monitoring_active:
            try:
                data = self.generate_simulated_data()

                with self.monitor_lock:
                    self.monitor_data.append(data)
                    # Keep only last 60 data points
                    if len(self.monitor_data) > 60:
                        self.monitor_data.pop(0)

                time.sleep(2)  # Update every 2 seconds
            except Exception as e:
                print(f"Monitor thread error: {e}")

    def start_monitoring(self):
        """Start real-time monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_data = []
            self.monitor_thread = threading.Thread(
                target=self.monitor_thread_worker, daemon=True
            )
            self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)

    def create_dashboard_tab(self):
        """Dashboard with KPI Overview"""
        self.tabs["dashboard"] = ctk.CTkFrame(self.content_frame)

        # Get data
        appliances = db.get_all_appliances()
        if appliances:
            total_load = calc.calculate_total_load(appliances)
            daily_consumption = calc.calculate_daily_consumption(appliances)
            corrected_energy = calc.calculate_corrected_energy(daily_consumption)
        else:
            total_load = daily_consumption = corrected_energy = 0

        # KPIs Section
        kpi_container = ctk.CTkFrame(self.tabs["dashboard"], fg_color="transparent")
        kpi_container.pack(fill="x", padx=10, pady=10)

        kpi1 = self.create_kpi_card(
            kpi_container, "Total Load", f"{total_load:.0f}", "W", "#00d4ff"
        )
        kpi1.pack(side="left", padx=10, fill="both", expand=True)

        kpi2 = self.create_kpi_card(
            kpi_container,
            "Daily Consumption",
            f"{daily_consumption / 1000:.2f}",
            "kWh",
            "#00ff88",
        )
        kpi2.pack(side="left", padx=10, fill="both", expand=True)

        kpi3 = self.create_kpi_card(
            kpi_container,
            "Corrected Energy",
            f"{corrected_energy / 1000:.2f}",
            "kWh",
            "#ffa500",
        )
        kpi3.pack(side="left", padx=10, fill="both", expand=True)

        kpi4 = self.create_kpi_card(
            kpi_container, "System Efficiency", "85", "%", "#00ff88"
        )
        kpi4.pack(side="left", padx=10, fill="both", expand=True)

        # Recent Logs Chart
        chart_label = ctk.CTkLabel(
            self.tabs["dashboard"],
            text="Recent Generation Logs",
            font=("Arial", 14, "bold"),
        )
        chart_label.pack(pady=(15, 5))

        logs = db.get_recent_logs()
        if logs:
            dates = [log[0] for log in logs]
            generation = [log[1] for log in logs]

            fig, ax = plt.subplots(figsize=(10, 3.5), facecolor="#2b2b2b")
            ax.set_facecolor("#1a1a1a")
            ax.bar(range(len(dates)), generation, color="#1f538d", alpha=0.8)
            ax.set_xticks(range(len(dates)))
            ax.set_xticklabels([d[-5:] for d in dates], rotation=45)
            ax.tick_params(colors="white", labelsize=9)
            ax.set_ylabel("Generation (kWh)", color="white")
            ax.set_title("Daily Energy Generation Trend", color="white")
            ax.grid(axis="y", alpha=0.2)

            canvas_frame = ctk.CTkFrame(self.tabs["dashboard"])
            canvas_frame.pack(fill="both", expand=True, padx=10, pady=5)

            canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
            canvas.get_tk_widget().pack(fill="both", expand=True)

    def create_analysis_tab(self):
        """System Analysis & Sizing Recommendations"""
        self.tabs["analysis"] = ctk.CTkFrame(self.content_frame)

        appliances = db.get_all_appliances()

        # Title
        title = ctk.CTkLabel(
            self.tabs["analysis"],
            text="System Sizing Analysis & Recommendations",
            font=("Arial", 16, "bold"),
        )
        title.pack(pady=15, padx=10)

        if appliances:
            # Create scrollable frame for analysis content
            scrollable_frame = ctk.CTkScrollableFrame(
                self.tabs["analysis"], fg_color="transparent"
            )
            scrollable_frame.pack(fill="both", expand=True, padx=10, pady=5)

            total_load = calc.calculate_total_load(appliances)
            daily_consumption = calc.calculate_daily_consumption(appliances)
            corrected_energy = calc.calculate_corrected_energy(daily_consumption)

            pv_power = calc.size_solar_pv(corrected_energy, peak_sun_hours=5.0)
            n_panels = calc.size_number_of_panels(pv_power, 350)
            battery_capacity = calc.size_battery_capacity(
                daily_consumption, 1.5, 24, 0.8
            )
            n_batteries = calc.size_number_of_batteries(battery_capacity, 200)
            inverter_power = calc.size_inverter(total_load, safety_factor=1.25)
            charge_controller_current = calc.size_charge_controller_current(
                pv_power, 24
            )

            # === SYSTEM SUMMARY SECTION ===
            summary_label = ctk.CTkLabel(
                scrollable_frame,
                text="📊 System Energy Summary",
                font=("Arial", 14, "bold"),
                text_color="#1f538d",
            )
            summary_label.pack(pady=(15, 10), padx=10, anchor="w")

            summary_container = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
            summary_container.pack(fill="x", padx=10, pady=5)

            summary_cards = [
                ("Total Load", f"{total_load:.0f}", "W", "#00d4ff"),
                (
                    "Daily Consumption",
                    f"{daily_consumption / 1000:.2f}",
                    "kWh",
                    "#00ff88",
                ),
                (
                    "Corrected Energy Need",
                    f"{corrected_energy / 1000:.2f}",
                    "kWh",
                    "#ffa500",
                ),
                ("System Efficiency", "85", "%", "#1f538d"),
            ]

            for label, value, unit, color in summary_cards:
                card = self.create_kpi_card(scrollable_frame, label, value, unit, color)
                card.pack(side="left", padx=5, fill="both", expand=True)

            # === COMPONENT SIZING SECTION ===
            component_label = ctk.CTkLabel(
                scrollable_frame,
                text="⚙️ Component Sizing Results",
                font=("Arial", 14, "bold"),
                text_color="#1f538d",
            )
            component_label.pack(pady=(20, 10), padx=10, anchor="w")

            component_container = ctk.CTkFrame(
                scrollable_frame, fg_color="#1a1a1a", corner_radius=10
            )
            component_container.pack(fill="x", padx=10, pady=10)

            components = [
                (
                    "Solar PV System",
                    f"{pv_power:.0f}",
                    "W",
                    "#00ff88",
                    "Total photovoltaic power output needed",
                ),
                (
                    "Number of Panels",
                    f"{n_panels}",
                    "× 350W",
                    "#ffa500",
                    "370W rated panels required",
                ),
                (
                    "Battery Capacity",
                    f"{battery_capacity:.0f}",
                    "Ah",
                    "#ff9500",
                    "Total usable capacity (24V system)",
                ),
                (
                    "Number of Batteries",
                    f"{n_batteries}",
                    "× 200Ah",
                    "#ffa500",
                    "Lithium cells with 80% DoD",
                ),
                (
                    "Inverter Size",
                    f"{inverter_power:.0f}",
                    "W",
                    "#00d4ff",
                    "1.25× safety factor applied",
                ),
                (
                    "Charge Controller",
                    f"{charge_controller_current:.1f}",
                    "A",
                    "#00ff88",
                    "MPPT recommended for efficiency",
                ),
            ]

            for i, (comp_name, value, unit, color, desc) in enumerate(components):
                comp_frame = ctk.CTkFrame(component_container, fg_color="transparent")
                comp_frame.pack(fill="x", padx=15, pady=8)

                name_label = ctk.CTkLabel(
                    comp_frame,
                    text=comp_name,
                    font=("Arial", 11, "bold"),
                    text_color="white",
                )
                name_label.pack(anchor="w")

                value_label = ctk.CTkLabel(
                    comp_frame,
                    text=f"{value} {unit}",
                    font=("Arial", 16, "bold"),
                    text_color=color,
                )
                value_label.pack(anchor="w", pady=2)

                desc_label = ctk.CTkLabel(
                    comp_frame, text=desc, font=("Arial", 9), text_color="#888888"
                )
                desc_label.pack(anchor="w")

            # === COMPONENT BREAKDOWN CHART ===
            chart_label = ctk.CTkLabel(
                scrollable_frame,
                text="📈 Component Breakdown",
                font=("Arial", 14, "bold"),
                text_color="#1f538d",
            )
            chart_label.pack(pady=(20, 10), padx=10, anchor="w")

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), facecolor="#2b2b2b")
            ax1.set_facecolor("#1a1a1a")
            ax2.set_facecolor("#1a1a1a")

            # Component cost estimation (realistic pricing)
            components_cost = [
                ("Solar Panels", n_panels * 150),
                ("Batteries", n_batteries * 2500),
                ("Inverter", inverter_power * 0.5),
                ("Charge Controller", charge_controller_current * 20),
                (
                    "Installation",
                    (n_panels * 150 + n_batteries * 2500 + inverter_power * 0.5) * 0.1,
                ),
            ]

            comp_names = [c[0] for c in components_cost]
            comp_costs = [c[1] for c in components_cost]
            colors_chart = ["#1f538d", "#00ff88", "#ffa500", "#00d4ff", "#ff6b6b"]

            ax1.pie(
                comp_costs,
                labels=comp_names,
                autopct="%1.1f%%",
                colors=colors_chart,
                startangle=90,
            )
            ax1.set_title(
                "System Cost Distribution",
                color="white",
                fontsize=12,
                fontweight="bold",
            )

            # Power requirements by component
            power_components = [
                "Solar\nPV",
                "Battery\nCapacity",
                "Inverter",
                "Load\nDemand",
            ]
            power_values = [
                pv_power,
                battery_capacity * 24 / 1000,
                inverter_power,
                total_load,
            ]

            bars = ax2.bar(
                power_components,
                power_values,
                color=["#00ff88", "#ffa500", "#00d4ff", "#ff9500"],
                alpha=0.8,
            )
            ax2.tick_params(colors="white", labelsize=10)
            ax2.set_ylabel("Power / Capacity", color="white")
            ax2.set_title(
                "Component Power Ratings", color="white", fontsize=12, fontweight="bold"
            )
            ax2.grid(axis="y", alpha=0.2)

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax2.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height,
                    f"{height:.0f}",
                    ha="center",
                    va="bottom",
                    color="white",
                    fontsize=9,
                )

            canvas_frame = ctk.CTkFrame(scrollable_frame)
            canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

            canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
            canvas.get_tk_widget().pack(fill="both", expand=True)

            # === COST SUMMARY SECTION ===
            cost_label = ctk.CTkLabel(
                scrollable_frame,
                text="💰 Cost Estimate Summary",
                font=("Arial", 14, "bold"),
                text_color="#1f538d",
            )
            cost_label.pack(pady=(20, 10), padx=10, anchor="w")

            cost_container = ctk.CTkFrame(
                scrollable_frame, fg_color="#1a1a1a", corner_radius=10
            )
            cost_container.pack(fill="x", padx=10, pady=10)

            total_cost = sum(c[1] for c in components_cost)

            for comp, cost in components_cost:
                cost_row = ctk.CTkFrame(cost_container, fg_color="transparent")
                cost_row.pack(fill="x", padx=15, pady=5)

                comp_label = ctk.CTkLabel(
                    cost_row, text=comp, font=("Arial", 11), text_color="white"
                )
                comp_label.pack(side="left", fill="x", expand=True)

                cost_text = ctk.CTkLabel(
                    cost_row,
                    text=f"₦{cost:,.0f}",
                    font=("Arial", 11, "bold"),
                    text_color="#00ff88",
                )
                cost_text.pack(side="right")

            separator = ctk.CTkFrame(cost_container, height=2, fg_color="#2b2b2b")
            separator.pack(fill="x", padx=15, pady=10)

            total_row = ctk.CTkFrame(cost_container, fg_color="transparent")
            total_row.pack(fill="x", padx=15, pady=10)

            total_label = ctk.CTkLabel(
                total_row,
                text="TOTAL PROJECT COST",
                font=("Arial", 12, "bold"),
                text_color="white",
            )
            total_label.pack(side="left", fill="x", expand=True)

            total_cost_text = ctk.CTkLabel(
                total_row,
                text=f"₦{total_cost:,.0f}",
                font=("Arial", 14, "bold"),
                text_color="#ffa500",
            )
            total_cost_text.pack(side="right")

            # === RECOMMENDATIONS SECTION ===
            rec_label = ctk.CTkLabel(
                scrollable_frame,
                text="✅ System Recommendations",
                font=("Arial", 14, "bold"),
                text_color="#1f538d",
            )
            rec_label.pack(pady=(20, 10), padx=10, anchor="w")

            rec_container = ctk.CTkFrame(
                scrollable_frame, fg_color="#1a1a1a", corner_radius=10
            )
            rec_container.pack(fill="x", padx=10, pady=10)

            recommendations = [
                f"✓ Use {n_panels} solar panels of 350W each for {pv_power:.0f}W total output",
                f"✓ Install {n_batteries} lithium batteries (200Ah) for {battery_capacity:.0f}Ah capacity",
                f"✓ Deploy {inverter_power:.0f}W inverter with built-in protection circuits",
                f"✓ Use MPPT charge controller rated for {charge_controller_current:.1f}A minimum",
                "✓ Maintain 1.5 days autonomy for critical load periods",
                "✓ Use 24V DC system configuration for optimal efficiency",
                "✓ Install DC disconnects and AC breaker protection",
                "✓ Monitor system daily for optimal performance",
            ]

            for rec in recommendations:
                rec_text = ctk.CTkLabel(
                    rec_container,
                    text=rec,
                    font=("Arial", 10),
                    text_color="#00ff88",
                    justify="left",
                    wraplength=500,
                )
                rec_text.pack(anchor="w", padx=15, pady=5)

        else:
            info = ctk.CTkLabel(
                self.tabs["analysis"],
                text="No appliances configured. Add appliances in Load Management tab.",
                font=("Arial", 12),
                text_color="#888888",
            )
            info.pack(pady=20)

    def create_monitor_tab(self):
        """Real-time Monitoring with Live Data Updates"""
        self.tabs["monitor"] = ctk.CTkFrame(self.content_frame)

        # --- Top Control Bar ---
        control_bar = ctk.CTkFrame(self.tabs["monitor"], fg_color="#1a1a1a", height=60)
        control_bar.pack(fill="x", padx=10, pady=10)

        title = ctk.CTkLabel(
            control_bar,
            text="⚡ Real-time System Monitor",
            font=("Arial", 14, "bold"),
        )
        title.pack(side="left", padx=15, pady=10)

        # Start/Stop buttons
        self.monitor_status_label = ctk.CTkLabel(
            control_bar,
            text="● Status: Idle",
            font=("Arial", 11),
            text_color="#ff6b6b",
        )
        self.monitor_status_label.pack(side="left", padx=20, pady=10)

        start_btn = ctk.CTkButton(
            control_bar,
            text="▶ Start Monitoring",
            width=120,
            command=self.start_monitoring,
            fg_color="#00ff88",
            text_color="#000000",
            hover_color="#00dd77",
        )
        start_btn.pack(side="left", padx=5, pady=10)

        stop_btn = ctk.CTkButton(
            control_bar,
            text="⏹ Stop Monitoring",
            width=120,
            command=self.stop_monitoring,
            fg_color="#ff6b6b",
            hover_color="#ff5a5a",
        )
        stop_btn.pack(side="left", padx=5, pady=10)

        # Refresh rate label
        refresh_label = ctk.CTkLabel(
            control_bar,
            text="Updating every 2 seconds",
            font=("Arial", 9),
            text_color="#888888",
        )
        refresh_label.pack(side="right", padx=15, pady=10)

        # --- Main Scrollable Content ---
        scrollable_frame = ctk.CTkScrollableFrame(
            self.tabs["monitor"], fg_color="transparent"
        )
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # --- Live Data Status Section ---
        status_title = ctk.CTkLabel(
            scrollable_frame,
            text="📊 Live System Status",
            font=("Arial", 14, "bold"),
            text_color="#1f538d",
        )
        status_title.pack(pady=(15, 10), padx=10, anchor="w")

        self.monitor_status_frame = ctk.CTkFrame(
            scrollable_frame, fg_color="#1a1a1a", corner_radius=10
        )
        self.monitor_status_frame.pack(fill="both", padx=10, pady=5)

        # Create live data display labels
        self.live_data_labels = {}
        live_metrics = [
            ("timestamp", "🕐 Timestamp", "#888888"),
            ("irradiance", "☀️ Solar Irradiance", "#ffa500"),
            ("generation", "⚡ Power Generation", "#00ff88"),
            ("load", "📱 Load Consumption", "#ff9500"),
            ("efficiency", "📈 System Efficiency", "#00d4ff"),
            ("balance", "⚖️ Energy Balance", "#1f538d"),
        ]

        for key, label, color in live_metrics:
            frame = ctk.CTkFrame(self.monitor_status_frame, fg_color="transparent")
            frame.pack(fill="x", padx=15, pady=8)

            label_widget = ctk.CTkLabel(
                frame, text=label, font=("Arial", 11), text_color=color
            )
            label_widget.pack(side="left", fill="x", expand=True)

            value_widget = ctk.CTkLabel(
                frame, text="-- --", font=("Arial", 12, "bold"), text_color="#ffffff"
            )
            value_widget.pack(side="right", padx=10)

            self.live_data_labels[key] = value_widget

        # --- Real-time Charts Section ---
        chart_title = ctk.CTkLabel(
            scrollable_frame,
            text="📈 Real-time Performance Graphs",
            font=("Arial", 14, "bold"),
            text_color="#1f538d",
        )
        chart_title.pack(pady=(20, 10), padx=10, anchor="w")

        self.chart_frame = ctk.CTkFrame(scrollable_frame)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # --- System Alerts Section ---
        alerts_title = ctk.CTkLabel(
            scrollable_frame,
            text="🔔 System Alerts & Notifications",
            font=("Arial", 14, "bold"),
            text_color="#1f538d",
        )
        alerts_title.pack(pady=(20, 10), padx=10, anchor="w")

        self.alerts_frame = ctk.CTkFrame(
            scrollable_frame, fg_color="#1a1a1a", corner_radius=10
        )
        self.alerts_frame.pack(fill="both", padx=10, pady=5)

        self.alerts_label = ctk.CTkLabel(
            self.alerts_frame,
            text="✓ System operating normally. Start monitoring to see real-time alerts.",
            font=("Arial", 10),
            text_color="#00ff88",
            justify="left",
            wraplength=600,
        )
        self.alerts_label.pack(padx=15, pady=15)

        # Schedule periodic updates
        self.update_monitor_display()

    def update_monitor_display(self):
        """Update monitor display with real-time data"""
        if self.current_tab == "monitor":
            with self.monitor_lock:
                if self.monitor_data:
                    latest = self.monitor_data[-1]

                    # Update status indicator
                    if self.monitoring_active:
                        self.monitor_status_label.configure(
                            text="● Status: Live", text_color="#00ff88"
                        )

                    # Update live data labels
                    self.live_data_labels["timestamp"].configure(
                        text=f"{latest['timestamp']}"
                    )
                    self.live_data_labels["irradiance"].configure(
                        text=f"{latest['irradiance']:.2f} kWh/m²"
                    )
                    self.live_data_labels["generation"].configure(
                        text=f"{latest['generation']:.2f} kWh"
                    )
                    self.live_data_labels["load"].configure(
                        text=f"{latest['load']:.2f} kWh"
                    )
                    self.live_data_labels["efficiency"].configure(
                        text=f"{latest['efficiency']:.1f}%"
                    )

                    # Balance with color coding
                    balance = latest["balance"]
                    balance_text = f"{abs(balance):.2f} kWh {'Surplus' if balance > 0 else 'Deficit'}"
                    balance_color = "#00ff88" if balance > 0 else "#ff6b6b"
                    self.live_data_labels["balance"].configure(
                        text=balance_text, text_color=balance_color
                    )

                    # Update charts
                    self.update_monitor_charts()

                    # Generate alerts
                    self.update_alerts(latest)

        # Schedule next update
        self.after(2000, self.update_monitor_display)

    def update_monitor_charts(self):
        """Update real-time charts with live data"""
        if len(self.monitor_data) < 2:
            return

        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        irradiance_data = [d["irradiance"] for d in self.monitor_data[-30:]]
        generation_data = [d["generation"] for d in self.monitor_data[-30:]]
        load_data = [d["load"] for d in self.monitor_data[-30:]]

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(
            2, 2, figsize=(12, 6), facecolor="#2b2b2b"
        )

        # Irradiance chart
        ax1.set_facecolor("#1a1a1a")
        ax1.plot(
            range(len(irradiance_data)),
            irradiance_data,
            color="#ffa500",
            linewidth=2,
            marker="o",
        )
        ax1.fill_between(
            range(len(irradiance_data)), irradiance_data, alpha=0.3, color="#ffa500"
        )
        ax1.set_title("Solar Irradiance", color="white", fontsize=11, fontweight="bold")
        ax1.set_ylabel("kWh/m²", color="white")
        ax1.tick_params(colors="white", labelsize=8)
        ax1.grid(alpha=0.2)

        # Generation chart
        ax2.set_facecolor("#1a1a1a")
        ax2.plot(
            range(len(generation_data)),
            generation_data,
            color="#00ff88",
            linewidth=2,
            marker="o",
        )
        ax2.fill_between(
            range(len(generation_data)), generation_data, alpha=0.3, color="#00ff88"
        )
        ax2.set_title("Power Generation", color="white", fontsize=11, fontweight="bold")
        ax2.set_ylabel("kWh", color="white")
        ax2.tick_params(colors="white", labelsize=8)
        ax2.grid(alpha=0.2)

        # Load chart
        ax3.set_facecolor("#1a1a1a")
        ax3.plot(
            range(len(load_data)), load_data, color="#ff9500", linewidth=2, marker="s"
        )
        ax3.fill_between(range(len(load_data)), load_data, alpha=0.3, color="#ff9500")
        ax3.set_title("Load Consumption", color="white", fontsize=11, fontweight="bold")
        ax3.set_ylabel("kWh", color="white")
        ax3.tick_params(colors="white", labelsize=8)
        ax3.grid(alpha=0.2)

        # Generation vs Load comparison
        ax4.set_facecolor("#1a1a1a")
        x = range(len(generation_data))
        ax4.plot(x, generation_data, color="#00ff88", label="Generation", linewidth=2)
        ax4.plot(x, load_data, color="#ff9500", label="Load", linewidth=2)
        ax4.fill_between(x, generation_data, load_data, alpha=0.2, color="#1f538d")
        ax4.set_title(
            "Generation vs Load", color="white", fontsize=11, fontweight="bold"
        )
        ax4.set_ylabel("kWh", color="white")
        ax4.tick_params(colors="white", labelsize=8)
        ax4.legend(loc="upper left", facecolor="#1a1a1a", edgecolor="white", fontsize=9)
        ax4.grid(alpha=0.2)

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_alerts(self, latest_data):
        """Generate system alerts based on real-time data"""
        alerts = []

        if latest_data["irradiance"] == 0:
            alerts.append(
                "☀️ No solar irradiance detected - Night time or cloudy conditions"
            )
        elif latest_data["irradiance"] > 4.5:
            alerts.append(
                "☀️ Peak solar irradiance detected - System performing optimally"
            )

        if latest_data["generation"] < latest_data["load"]:
            alerts.append(
                f"⚠️ DEFICIT: Load ({latest_data['load']:.2f}) exceeds generation ({latest_data['generation']:.2f}) kWh"
            )
        elif latest_data["balance"] > 1.0:
            alerts.append(
                f"✓ Surplus energy: {latest_data['balance']:.2f} kWh available for storage"
            )

        if latest_data["efficiency"] > 0 and latest_data["efficiency"] < 70:
            alerts.append(
                f"⚠️ Low efficiency ({latest_data['efficiency']:.1f}%) - Check panel condition"
            )
        elif latest_data["efficiency"] > 85:
            alerts.append(f"✓ Excellent efficiency ({latest_data['efficiency']:.1f}%)")

        if not alerts:
            alerts.append(
                "✓ System operating normally. All parameters within acceptable range."
            )

        # Update alerts display
        alert_text = "\n".join(alerts)
        self.alerts_label.configure(text=alert_text)

    def create_loads_tab(self):
        """Load Management"""
        self.tabs["loads"] = ctk.CTkFrame(self.content_frame)

        title = ctk.CTkLabel(
            self.tabs["loads"], text="Load Management", font=("Arial", 16, "bold")
        )
        title.pack(pady=15, padx=10)

        appliances = db.get_all_appliances()

        if appliances:
            # Appliances List
            list_frame = ctk.CTkFrame(self.tabs["loads"], fg_color="#1a1a1a")
            list_frame.pack(fill="both", expand=True, padx=10, pady=10)

            header_frame = ctk.CTkFrame(list_frame, fg_color="#2b2b2b", height=40)
            header_frame.pack(fill="x", padx=5, pady=5)

            headers = ["Name", "Power (W)", "Hours/Day", "Qty", "Daily (Wh)"]
            for i, header in enumerate(headers):
                ctk.CTkLabel(
                    header_frame,
                    text=header,
                    font=("Arial", 11, "bold"),
                    text_color="#888888",
                ).pack(side="left", padx=10, fill="both", expand=True)

            for app in appliances:
                app_frame = ctk.CTkFrame(list_frame, fg_color="#0d0d0d")
                app_frame.pack(fill="x", padx=5, pady=3)

                daily_wh = app["power"] * app["hours"] * app["quantity"]
                values = [
                    app["name"],
                    f"{app['power']}",
                    f"{app['hours']}",
                    f"{app['quantity']}",
                    f"{daily_wh:.0f}",
                ]

                for value in values:
                    ctk.CTkLabel(app_frame, text=str(value), font=("Arial", 10)).pack(
                        side="left", padx=10, fill="both", expand=True
                    )
        else:
            info = ctk.CTkLabel(
                self.tabs["loads"],
                text="No appliances configured yet.",
                font=("Arial", 12),
                text_color="#888888",
            )
            info.pack(pady=20)

    def create_reports_tab(self):
        """Historical Reports"""
        self.tabs["reports"] = ctk.CTkFrame(self.content_frame)

        title = ctk.CTkLabel(
            self.tabs["reports"],
            text="Historical Reports & Analytics",
            font=("Arial", 16, "bold"),
        )
        title.pack(pady=15, padx=10)

        logs = db.get_all_logs()
        if logs:
            # Summary Statistics
            total_gen = sum(log[1] for log in logs)
            total_consumed = sum(log[2] for log in logs)
            avg_irradiance = sum(log[3] for log in logs) / len(logs) if logs else 0

            stats_container = ctk.CTkFrame(self.tabs["reports"], fg_color="transparent")
            stats_container.pack(fill="x", padx=10, pady=10)

            self.create_kpi_card(
                stats_container,
                "Total Generation",
                f"{total_gen:.1f}",
                "kWh",
                "#00ff88",
            ).pack(side="left", padx=10, fill="both", expand=True)
            self.create_kpi_card(
                stats_container,
                "Total Consumed",
                f"{total_consumed:.1f}",
                "kWh",
                "#ffa500",
            ).pack(side="left", padx=10, fill="both", expand=True)
            self.create_kpi_card(
                stats_container,
                "Avg Irradiance",
                f"{avg_irradiance:.2f}",
                "kWh/m²",
                "#00d4ff",
            ).pack(side="left", padx=10, fill="both", expand=True)

            # Historical Chart
            dates = [log[0] for log in logs]
            gen_data = [log[1] for log in logs]
            load_data = [log[2] for log in logs]

            fig, ax = plt.subplots(figsize=(10, 4), facecolor="#2b2b2b")
            ax.set_facecolor("#1a1a1a")

            x = range(len(dates))
            ax.plot(
                x,
                gen_data,
                marker="o",
                label="Generation",
                color="#00ff88",
                linewidth=2,
            )
            ax.plot(
                x, load_data, marker="s", label="Load", color="#ffa500", linewidth=2
            )
            ax.fill_between(x, gen_data, load_data, alpha=0.2, color="#1f538d")

            ax.set_xticks(x)
            ax.set_xticklabels([d[-5:] for d in dates], rotation=45)
            ax.tick_params(colors="white", labelsize=9)
            ax.set_ylabel("Energy (kWh)", color="white")
            ax.legend(loc="upper left", facecolor="#1a1a1a", edgecolor="white")
            ax.grid(alpha=0.2)

            canvas_frame = ctk.CTkFrame(self.tabs["reports"])
            canvas_frame.pack(fill="both", expand=True, padx=10, pady=5)

            canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
            canvas.get_tk_widget().pack(fill="both", expand=True)


if __name__ == "__main__":
    app = SolarAnalyzerApp()
    app.mainloop()
