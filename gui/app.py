import customtkinter as ctk
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from .plot_logic import PlotLogicMixin

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ModernSegmentApp(ctk.CTk, PlotLogicMixin):
    def __init__(self):
        super().__init__()
        self.title("Intersection Solver - Professional")
        self.geometry("1100x780")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Init state
        self.dragged_point_index = None 
        self.is_panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.shift_pressed = False 
        self.history = [] 
        self.history_index = -1 
        self.is_history_restoring = False 
        self.entries = {}

        # --- GUI Setup ---
        self.sidebar_frame = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        ctk.CTkLabel(self.sidebar_frame, text="Geometria Analityczna", 
                     font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        
        ctk.CTkLabel(self.sidebar_frame, text="LPM: Przesuwanie / Pan\nSHIFT + Drag: ORTHO\nScroll: Zoom",
                     text_color="gray70").grid(row=1, column=0, padx=20, pady=(0, 20))

        self.create_inputs()
        self.create_controls()
        self.create_status_card()

        self.plot_container = ctk.CTkFrame(self, fg_color="transparent")
        self.plot_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.init_plot()
        self.update_graph()
        self.reset_view()
        self.save_history_snapshot(force=True)

        self.bind("<KeyPress-Shift_L>", self.on_shift_press)
        self.bind("<KeyPress-Shift_R>", self.on_shift_press)
        self.bind("<KeyRelease-Shift_L>", self.on_shift_release)
        self.bind("<KeyRelease-Shift_R>", self.on_shift_release)

    def create_inputs(self):
        self.seg1_frame = ctk.CTkFrame(self.sidebar_frame)
        self.seg1_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(self.seg1_frame, text="Odcinek 1 (Niebieski)", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.add_coord_row(self.seg1_frame, "Początek (x1, y1)", "x1", "y1", 0, 0)
        self.add_coord_row(self.seg1_frame, "Koniec (x2, y2)", "x2", "y2", 0, 4)

        self.seg2_frame = ctk.CTkFrame(self.sidebar_frame)
        self.seg2_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(self.seg2_frame, text="Odcinek 2 (Fioletowy)", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.add_coord_row(self.seg2_frame, "Początek (x3, y3)", "x3", "y3", 0, 4)
        self.add_coord_row(self.seg2_frame, "Koniec (x4, y4)", "x4", "y4", 4, 0)

    def add_coord_row(self, parent, title, k1, k2, v1, v2):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(row, text=title, font=ctk.CTkFont(size=11)).pack(anchor="w")
        box = ctk.CTkFrame(row, fg_color="transparent")
        box.pack(fill="x", pady=2)
        for key, val in [(k1, v1), (k2, v2)]:
            e = ctk.CTkEntry(box, width=60)
            e.insert(0, str(val))
            e.pack(side="left", padx=5, expand=True, fill="x")
            e.bind("<KeyRelease>", self.update_graph)
            e.bind("<FocusOut>", lambda e: self.save_history_snapshot())
            self.entries[key] = e

    def create_controls(self):
        self.controls_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.controls_frame.grid(row=8, column=0, padx=20, pady=10, sticky="ew")

        self.infinite_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(self.controls_frame, text="Nieskończone proste", 
                      variable=self.infinite_var, command=self.update_graph).pack(anchor="w", pady=5)

        self.snap_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.snap_frame.pack(fill="x", pady=(0, 10))
        self.snap_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(self.snap_frame, text="Snap:", variable=self.snap_var, width=50).pack(side="left")
        self.snap_entry = ctk.CTkEntry(self.snap_frame, width=60, placeholder_text="0.5")
        self.snap_entry.insert(0, "0.5")
        self.snap_entry.pack(side="left", padx=10)

        h_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        h_frame.pack(fill="x")
        ctk.CTkButton(h_frame, text="< Cofnij", width=80, command=self.undo_action, 
                      fg_color="#3a3a3a", hover_color="#555555").pack(side="left", padx=(0,5))
        ctk.CTkButton(h_frame, text="Ponów >", width=80, command=self.redo_action, 
                      fg_color="#3a3a3a", hover_color="#555555").pack(side="left")

        ctk.CTkButton(self.controls_frame, text="Zapisz Wykres", command=self.save_figure, 
                      fg_color="#1f6aa5").pack(fill="x", pady=(10, 0))

    def create_status_card(self):
        self.status_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.status_container.grid(row=9, column=0, padx=20, pady=20, sticky="ew")
        
        ctk.CTkLabel(self.status_container, text="WYNIK OBLICZEŃ", 
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="gray60").pack(anchor="w", pady=(0,5))

        self.status_card = ctk.CTkFrame(self.status_container, fg_color="#444444", corner_radius=10)
        self.status_card.pack(fill="x", ipady=10)

        self.lbl_status_main = ctk.CTkLabel(self.status_card, text="BRAK DANYCH", 
                                            font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
        self.lbl_status_main.pack(expand=True)
        self.lbl_status_sub = ctk.CTkLabel(self.status_card, text="...", 
                                           font=ctk.CTkFont(size=13), text_color="#E0E0E0")
        self.lbl_status_sub.pack(expand=True)

    def init_plot(self):
        bg_color = "#2b2b2b"
        self.fig = Figure(figsize=(5, 5), dpi=100)
        self.fig.patch.set_facecolor(bg_color)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(bg_color)
        self.ax.tick_params(colors='white', which='both')
        for spine in self.ax.spines.values(): spine.set_color('gray')

        self.tooltip = self.ax.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                                        bbox=dict(boxstyle="round", fc="#2b2b2b", ec="white", alpha=0.9),
                                        color="white", fontsize=9)
        self.tooltip.set_visible(False)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_container)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_drag)
        self.canvas.mpl_connect('scroll_event', self.on_scroll_zoom)