import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
#import calculations as calc

class SolarAnalyzerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PV Component Analyzer & Monitor")
        self.geometry("1000x600")
        ctk.set_appearance_mode("dark")
        
        # --- Sidebar Navigation ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        self.title_label = ctk.CTkLabel(self.sidebar, text="Solar Analyzer", font=("Arial", 20, "bold"))
        self.title_label.pack(pady=20, padx=10)
        
        # --- Main Content Area ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        self.load_dashboard()

    def load_dashboard(self):
        # Example KPI Card
        self.kpi_card = ctk.CTkFrame(self.main_frame, width=250, height=100)
        self.kpi_card.grid(row=0, column=0, padx=10, pady=10)
        
        self.kpi_label = ctk.CTkLabel(self.kpi_card, text="Expected Efficiency\n85%", font=("Arial", 16))
        self.kpi_label.center() # places it neatly
        self.kpi_label.pack(pady=20)

        # Matplotlib Chart Integration
        fig, ax = plt.subplots(figsize=(5, 3), facecolor='#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        ax.plot([1, 2, 3, 4], [10, 25, 35, 30], color="#1f538d", marker='o')
        ax.tick_params(colors='white')
        ax.set_title("Daily Energy Generation (kWh)", color="white")
        
        canvas = FigureCanvasTkAgg(fig, master=self.main_frame)
        canvas.get_tk_widget().grid(row=1, column=0, columnspan=2, padx=10, pady=10)

if __name__ == "__main__":
    app = SolarAnalyzerApp()
    app.mainloop()