import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import calculations as calc
import database as db
import recommendations as rec


class SolarAnalyzerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PV Component Analyzer & Monitor")
        self.geometry("1400x800")
        ctk.set_appearance_mode("dark")

        # Initialize database
        db.init_db()

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
            text="System Sizing Analysis",
            font=("Arial", 16, "bold"),
        )
        title.pack(pady=15, padx=10)

        # Calculate sizing
        if appliances:
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

            # Sizing Results in Grid
            results_container = ctk.CTkFrame(
                self.tabs["analysis"], fg_color="transparent"
            )
            results_container.pack(fill="both", expand=True, padx=10, pady=10)

            results = [
                ("Solar PV Power Required", f"{pv_power:.0f}", "W"),
                ("Number of Panels (350W)", f"{n_panels}", "units"),
                ("Battery Capacity Required", f"{battery_capacity:.0f}", "Ah"),
                ("Number of Batteries (200Ah)", f"{n_batteries}", "units"),
                ("Inverter Size Required", f"{inverter_power:.0f}", "W"),
            ]

            for i, (label, value, unit) in enumerate(results):
                row = i % 2
                col = i // 2
                card = self.create_kpi_card(
                    results_container, label, value, unit, "#1f538d"
                )
                card.grid(row=row, column=col, padx=10, pady=10, sticky="ew")

            results_container.grid_columnconfigure(0, weight=1)
            results_container.grid_columnconfigure(1, weight=1)
        else:
            info = ctk.CTkLabel(
                self.tabs["analysis"],
                text="No appliances configured. Add appliances in Load Management tab.",
                font=("Arial", 12),
                text_color="#888888",
            )
            info.pack(pady=20)

    def create_monitor_tab(self):
        """Real-time Monitoring"""
        self.tabs["monitor"] = ctk.CTkFrame(self.content_frame)

        title = ctk.CTkLabel(
            self.tabs["monitor"],
            text="Real-time System Monitor",
            font=("Arial", 16, "bold"),
        )
        title.pack(pady=15, padx=10)

        logs = db.get_recent_logs()
        if logs:
            # Latest log info
            latest = logs[-1]
            status_frame = ctk.CTkFrame(
                self.tabs["monitor"], fg_color="#1a1a1a", corner_radius=10
            )
            status_frame.pack(fill="x", padx=10, pady=10)

            status_info = f"Date: {latest[0]} | Irradiance: {latest[1]:.1f} kWh/m² | Generation: {latest[2]:.2f} kWh | Load: {latest[3]:.2f} kWh"
            status_label = ctk.CTkLabel(
                status_frame, text=status_info, font=("Arial", 12), text_color="#00ff88"
            )
            status_label.pack(pady=10, padx=10)

            # Performance Indicators
            kpi_container = ctk.CTkFrame(self.tabs["monitor"], fg_color="transparent")
            kpi_container.pack(fill="x", padx=10, pady=10)

            efficiency = (latest[2] / (latest[1] * 10)) * 100 if latest[1] > 0 else 0
            balance = latest[2] - latest[3]
            balance_status = "Surplus" if balance > 0 else "Deficit"
            balance_color = "#00ff88" if balance > 0 else "#ff6b6b"

            self.create_kpi_card(
                kpi_container, "Current Efficiency", f"{efficiency:.1f}", "%", "#00d4ff"
            ).pack(side="left", padx=10, fill="both", expand=True)
            self.create_kpi_card(
                kpi_container,
                "Generation (Today)",
                f"{latest[2]:.2f}",
                "kWh",
                "#00ff88",
            ).pack(side="left", padx=10, fill="both", expand=True)
            self.create_kpi_card(
                kpi_container, "Load Consumed", f"{latest[3]:.2f}", "kWh", "#ffa500"
            ).pack(side="left", padx=10, fill="both", expand=True)
            self.create_kpi_card(
                kpi_container,
                f"Energy {balance_status}",
                f"{abs(balance):.2f}",
                "kWh",
                balance_color,
            ).pack(side="left", padx=10, fill="both", expand=True)

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
