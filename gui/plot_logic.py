import math
import tkinter as tk
from tkinter import filedialog
from logic.algorithm import find_intersection
from logic.math_utils import get_line_equation, distance_point_to_segment

class PlotLogicMixin:
    """Logika wykresu, obsługa myszki, historia i funkcje pomocnicze."""

    # --- HELPERS ---
    def get_coords(self):
        try:
            vals = []
            for lbl in ['x1', 'y1', 'x2', 'y2', 'x3', 'y3', 'x4', 'y4']:
                val = self.entries[lbl].get().replace(',', '.')
                vals.append(float(val))
            return vals
        except ValueError:
            return None

    def set_coord(self, label, value):
        self.entries[label].delete(0, tk.END)
        self.entries[label].insert(0, f"{value:.2f}")

    def get_safe_limits(self, values, min_span=4.0):
        if not values: return 0, 10
        min_v, max_v = min(values), max(values)
        span = max_v - min_v
        if span < min_span:
            mid = (max_v + min_v) / 2
            return mid - (min_span / 2), mid + (min_span / 2)
        else:
            margin = span * 0.15
            return min_v - margin, max_v + margin

    def get_snap_value(self):
        try:
            val = float(self.snap_entry.get().replace(',', '.'))
            return val if val > 0 else 0.5
        except ValueError:
            return 0.5

    def save_figure(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG file", "*.png"), ("All files", "*.*")])
        if file_path:
            self.fig.savefig(file_path)

    def reset_view(self):
        coords = self.get_coords()
        if coords:
            all_x = [coords[0], coords[2], coords[4], coords[6]]
            all_y = [coords[1], coords[3], coords[5], coords[7]]
            x_min, x_max = self.get_safe_limits(all_x)
            y_min, y_max = self.get_safe_limits(all_y)
            self.ax.set_xlim(x_min, x_max)
            self.ax.set_ylim(y_min, y_max)
            self.ax.set_aspect('equal', adjustable='box')
            self.canvas.draw()

    # --- HISTORIA ---
    def save_history_snapshot(self, force=False):
        if self.is_history_restoring: return
        current_coords = self.get_coords()
        if current_coords is None: return
        if not force and self.history:
            if self.history[self.history_index] == current_coords: return 
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        self.history.append(current_coords)
        self.history_index += 1
        if len(self.history) > 50:
            self.history.pop(0)
            self.history_index -= 1

    def undo_action(self):
        if self.history_index > 0:
            self.is_history_restoring = True
            self.history_index -= 1
            prev_coords = self.history[self.history_index]
            self.apply_coords(prev_coords)
            self.update_graph()
            self.is_history_restoring = False

    def redo_action(self):
        if self.history_index < len(self.history) - 1:
            self.is_history_restoring = True
            self.history_index += 1
            next_coords = self.history[self.history_index]
            self.apply_coords(next_coords)
            self.update_graph()
            self.is_history_restoring = False

    def apply_coords(self, coords):
        labels = ['x1', 'y1', 'x2', 'y2', 'x3', 'y3', 'x4', 'y4']
        for i, lbl in enumerate(labels):
            self.entries[lbl].delete(0, tk.END)
            self.entries[lbl].insert(0, f"{coords[i]:.2f}")

    # --- EVENTS (MOUSE & KEYBOARD) ---
    def on_shift_press(self, event): self.shift_pressed = True
    def on_shift_release(self, event): self.shift_pressed = False

    def on_scroll_zoom(self, event):
        base_scale = 1.1
        scale_factor = 1 / base_scale if event.button == 'up' else base_scale
        cur_xlim, cur_ylim = self.ax.get_xlim(), self.ax.get_ylim()
        
        if event.xdata is not None and event.ydata is not None:
            xdata, ydata = event.xdata, event.ydata
        else:
            inv = self.ax.transData.inverted()
            xdata, ydata = inv.transform((event.x, event.y))

        new_w = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_h = (cur_ylim[1] - cur_ylim[0]) * scale_factor
        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

        self.ax.set_xlim([xdata - new_w * (1 - relx), xdata + new_w * relx])
        self.ax.set_ylim([ydata - new_h * (1 - rely), ydata + new_h * rely])
        self.canvas.draw()

    def on_click(self, event):
        if event.button != 1: return
        if event.inaxes != self.ax: return
        coords = self.get_coords()
        if coords is None: return
        points = [(coords[0], coords[1]), (coords[2], coords[3]), 
                  (coords[4], coords[5]), (coords[6], coords[7])]
        click_point = (event.xdata, event.ydata)
        xlim = self.ax.get_xlim()
        threshold = (xlim[1] - xlim[0]) * 0.05 
        
        closest_dist = float('inf')
        closest_idx = None
        for i, p in enumerate(points):
            dist = math.hypot(p[0]-click_point[0], p[1]-click_point[1])
            if dist < closest_dist:
                closest_dist = dist
                closest_idx = i
        
        if closest_dist < threshold:
            self.dragged_point_index = closest_idx
        else:
            self.is_panning = True
            self.pan_start_x = event.x
            self.pan_start_y = event.y

    def on_release(self, event):
        if self.dragged_point_index is not None:
            self.save_history_snapshot()
        self.dragged_point_index = None
        self.is_panning = False

    def on_drag(self, event):
        # Tooltips (Hover)
        if self.dragged_point_index is None and not self.is_panning:
            if event.inaxes != self.ax:
                if self.tooltip.get_visible():
                    self.tooltip.set_visible(False)
                    self.canvas.draw()
                return
            coords = self.get_coords()
            if not coords: return
            
            P1, P2 = (coords[0], coords[1]), (coords[2], coords[3])
            P3, P4 = (coords[4], coords[5]), (coords[6], coords[7])
            cursor = (event.xdata, event.ydata)
            xlim = self.ax.get_xlim()
            thresh = (xlim[1] - xlim[0]) * 0.03
            
            found = False
            for p in [P1, P2, P3, P4]:
                if math.hypot(p[0]-cursor[0], p[1]-cursor[1]) < thresh:
                    self.tooltip.xy = p
                    self.tooltip.set_text(f"({p[0]:.2f}, {p[1]:.2f})")
                    self.tooltip.set_visible(True)
                    self.canvas.draw()
                    found = True
                    break
            if not found:
                for s, e, n in [(P1, P2, "L1"), (P3, P4, "L2")]:
                    if distance_point_to_segment(cursor, s, e) < thresh:
                        eq = get_line_equation(s, e)
                        self.tooltip.xy = cursor
                        self.tooltip.set_text(f"{n}: {eq}")
                        self.tooltip.set_visible(True)
                        self.canvas.draw()
                        found = True
                        break
            if not found and self.tooltip.get_visible():
                self.tooltip.set_visible(False)
                self.canvas.draw()
            return

        # Panning
        if self.is_panning:
            if event.inaxes != self.ax: return
            dx_pix = event.x - self.pan_start_x
            dy_pix = event.y - self.pan_start_y
            bbox = self.ax.get_window_extent()
            xlim, ylim = self.ax.get_xlim(), self.ax.get_ylim()
            width_data, height_data = xlim[1] - xlim[0], ylim[1] - ylim[0]
            dx_data = (dx_pix / bbox.width) * width_data
            dy_data = (dy_pix / bbox.height) * height_data
            self.ax.set_xlim(xlim[0] - dx_data, xlim[1] - dx_data)
            self.ax.set_ylim(ylim[0] - dy_data, ylim[1] - dy_data)
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            self.canvas.draw()
            return

        # Dragging
        if self.dragged_point_index is not None:
            if self.tooltip.get_visible(): self.tooltip.set_visible(False)
            mapping = [('x1', 'y1'), ('x2', 'y2'), ('x3', 'y3'), ('x4', 'y4')]
            keys = mapping[self.dragged_point_index]
            
            if event.xdata is not None and event.ydata is not None:
                x_new, y_new = event.xdata, event.ydata
            else:
                inv = self.ax.transData.inverted()
                x_new, y_new = inv.transform((event.x, event.y))

            if self.shift_pressed:
                coords = self.get_coords()
                if self.dragged_point_index == 0: anchor = (coords[2], coords[3])
                elif self.dragged_point_index == 1: anchor = (coords[0], coords[1])
                elif self.dragged_point_index == 2: anchor = (coords[6], coords[7])
                elif self.dragged_point_index == 3: anchor = (coords[4], coords[5])
                if abs(x_new - anchor[0]) > abs(y_new - anchor[1]): y_new = anchor[1]
                else: x_new = anchor[0]

            if self.snap_var.get():
                snap_val = self.get_snap_value()
                x_new = round(x_new / snap_val) * snap_val
                y_new = round(y_new / snap_val) * snap_val
            
            self.set_coord(keys[0], x_new)
            self.set_coord(keys[1], y_new)
            self.update_graph()

    # --- UPDATE GRAPH ---
    def update_graph(self, event=None):
        coords = self.get_coords()
        is_infinite = self.infinite_var.get()
        current_xlim = self.ax.get_xlim()
        current_ylim = self.ax.get_ylim()

        self.ax.clear()
        self.ax.set_facecolor("#2b2b2b")
        self.fig.patch.set_facecolor("#2b2b2b")
        self.ax.grid(True, linestyle=':', color='gray', alpha=0.3)
        self.ax.tick_params(colors='gray', labelcolor='white')
        for spine in self.ax.spines.values(): spine.set_color('#444444')
        self.ax.add_artist(self.tooltip)

        if coords is None:
            self.lbl_status_main.configure(text="BŁĄD DANYCH")
            self.status_card.configure(fg_color="#C0392B")
            self.canvas.draw()
            return

        P1, P2 = (coords[0], coords[1]), (coords[2], coords[3])
        P3, P4 = (coords[4], coords[5]), (coords[6], coords[7])

        res_type, res_data = find_intersection(P1, P2, P3, P4, infinite=is_infinite)

        if res_type == "POINT":
            self.lbl_status_main.configure(text="PRZECIĘCIE")
            self.lbl_status_sub.configure(text=f"X: {res_data[0]:.2f}   Y: {res_data[1]:.2f}")
            self.status_card.configure(fg_color="#27AE60")
        elif res_type == "SEGMENT":
            self.lbl_status_main.configure(text="WSPÓLNY ODCINEK")
            self.lbl_status_sub.configure(text="Nakładają się")
            self.status_card.configure(fg_color="#2980B9")
        else:
            self.lbl_status_main.configure(text="BRAK PRZECIĘCIA")
            self.lbl_status_sub.configure(text="")
            self.status_card.configure(fg_color="#C0392B")

        if is_infinite:
            self.ax.axline(P1, P2, color='#00E5FF', linewidth=2, alpha=0.6, label='Prosta 1')
            self.ax.plot([P1[0], P2[0]], [P1[1], P2[1]], color='#00E5FF', marker='o', linestyle='', markersize=8, picker=True)
            self.ax.axline(P3, P4, color='#E040FB', linewidth=2, alpha=0.6, label='Prosta 2')
            self.ax.plot([P3[0], P4[0]], [P3[1], P4[1]], color='#E040FB', marker='o', linestyle='', markersize=8, picker=True)
        else:
            self.ax.plot([P1[0], P2[0]], [P1[1], P2[1]], color='#00E5FF', marker='o', label='Odcinek 1', markersize=8, linewidth=2, alpha=0.8, picker=True)
            self.ax.plot([P3[0], P4[0]], [P3[1], P4[1]], color='#E040FB', marker='o', label='Odcinek 2', markersize=8, linewidth=2, alpha=0.8, picker=True)

        if res_type == "POINT":
            self.ax.plot(res_data[0], res_data[1], color='#FFFF00', marker='*', markersize=15, zorder=10, label='Przecięcie', markeredgecolor='black')
        elif res_type == "SEGMENT":
            s1, s2 = res_data
            self.ax.plot([s1[0], s2[0]], [s1[1], s2[1]], color='#FFFF00', linewidth=5, alpha=0.6, zorder=10, label='Wspólny odc.')

        self.ax.legend(facecolor='#333333', edgecolor='#333333', labelcolor='white')
        self.ax.set_xlim(current_xlim)
        self.ax.set_ylim(current_ylim)
        self.ax.set_aspect('equal', adjustable='box')
        self.canvas.draw()