import threading
import time
import math
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import os
import psutil

# Import your Pybind11-compiled C++ module, which supports multi-threading via OpenMP
import monte_carlo

MAX_POINTS_TO_PLOT = 10000

class MonteCarloApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monte Carlo Pi Estimation - Performance Demo")

        # ---------------
        # USER CONTROLS
        # ---------------
        self.running = False
        self.batch_size = 1000      # default batch size
        self.num_threads = 2        # default number of threads

        # ---------------
        # SIM STATS
        # ---------------
        self.total_points = 0
        self.inside_circle = 0
        self.start_time = None

        # Track points (for plotting)
        self.points_inside = []
        self.points_outside = []

        # ---------------
        # CONVERGENCE / SCORE
        # ---------------
        self.convergence_threshold = 1e-4
        self.consecutive_needed = 5  # must meet threshold 5 consecutive times
        self.consecutive_hits = 0
        self.converged = False
        self.convergence_time = None

        # We'll track peak memory usage
        self.peak_mem_usage_mb = 0.0

        # We'll display two scores:
        # 1) Time-to-Convergence (once stable)
        # 2) Aggregated Score (based on more factors)
        self.final_time_score = None
        self.final_agg_score = None

        # ---------------
        # SET UP FIGURE
        # ---------------
        self.fig = Figure(figsize=(5, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlim(-1, 1)
        self.ax.set_ylim(-1, 1)
        self.ax.set_aspect("equal")
        self.ax.set_title("Monte Carlo Pi Estimation")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # ---------------
        # CONTROL FRAME
        # ---------------
        control_frame = tk.Frame(root)
        control_frame.pack(pady=5)

        # Start/Stop Button
        self.button = tk.Button(control_frame, text="Start", command=self.toggle_simulation)
        self.button.pack(side=tk.LEFT, padx=5)

        # Batch Size
        tk.Label(control_frame, text="Batch Size:").pack(side=tk.LEFT)
        self.batch_entry = tk.Entry(control_frame, width=6)
        self.batch_entry.insert(0, str(self.batch_size))
        self.batch_entry.pack(side=tk.LEFT, padx=5)

        # Num Threads
        max_threads = monte_carlo.get_available_threads()
        # max_threads = os.cpu_count()

        tk.Label(control_frame, text="Threads (MAX " + str(max_threads) + ") :").pack(side=tk.LEFT)
        self.thread_entry = tk.Entry(control_frame, width=4)
        self.thread_entry.insert(0, str(self.num_threads))
        self.thread_entry.pack(side=tk.LEFT, padx=5)

        # ---------------
        # LABELS (KPIs)
        # ---------------
        self.label_pi = tk.Label(root, text="Estimated Pi: N/A")
        self.label_pi.pack()

        self.label_error = tk.Label(root, text="Absolute Error: N/A")
        self.label_error.pack()

        self.label_time = tk.Label(root, text="Time Elapsed: 0 s")
        self.label_time.pack()

        # Show current memory and peak memory
        self.label_mem_current = tk.Label(root, text="Current Mem Usage: 0 MB")
        self.label_mem_current.pack()
        self.label_mem_peak = tk.Label(root, text="Peak Mem Usage: 0 MB")
        self.label_mem_peak.pack()

        # Show time score (time-to-convergence) once stable
        self.label_time_score = tk.Label(root, text="Time-to-Convergence Score: N/A", fg="black")
        self.label_time_score.pack()

        # Show aggregated score
        self.label_agg_score = tk.Label(root, text="Aggregated Score: N/A", fg="black")
        self.label_agg_score.pack()

    def toggle_simulation(self):
        if self.running:
            # Stopping
            self.running = False
            self.button.config(text="Start")
        else:
            # Starting
            self.running = True
            self.button.config(text="Stop")

            # Read user inputs
            try:
                self.batch_size = int(self.batch_entry.get())
            except ValueError:
                self.batch_size = 1000

            try:
                self.num_threads = int(self.thread_entry.get())
            except ValueError:
                self.num_threads = 2

            # Set environment var (if using environment for OpenMP)
            os.environ["OMP_NUM_THREADS"] = str(self.num_threads)

            # If you have a function in the C++ module to set threads programmatically, you could do:
            # monte_carlo.set_num_threads(self.num_threads)

            # Reset stats
            self.total_points = 0
            self.inside_circle = 0
            self.points_inside.clear()
            self.points_outside.clear()

            self.converged = False
            self.convergence_time = None
            self.consecutive_hits = 0
            self.peak_mem_usage_mb = 0.0

            self.final_time_score = None
            self.final_agg_score = None

            self.start_time = time.time()

            # Kick off in a separate thread
            threading.Thread(target=self.run_simulation, daemon=True).start()

    def run_simulation(self):
        """ Continuously run simulation while self.running is True. """
        while self.running:
            # Generate a batch of random points from C++
            # points = monte_carlo.monte_carlo_step_std(num_points=10000, num_threads=4)
            points = monte_carlo.monte_carlo_step_std(self.batch_size, self.num_threads)

            for x, y, inside in points:
                if inside:
                    self.points_inside.append((x, y))
                    if len(self.points_inside) > MAX_POINTS_TO_PLOT:
                        self.points_inside.pop(0)
                    self.inside_circle += 1
                else:
                    self.points_outside.append((x, y))
                    if len(self.points_outside) > MAX_POINTS_TO_PLOT:
                        self.points_outside.pop(0)
                self.total_points += 1

            # Update the UI (plots + KPIs)
            self.update_plot()

            # Optional short sleep if you want to limit CPU usage or UI updates
            # time.sleep(0.01)

    def update_plot(self):
        """ Update the plot and the KPI labels. """
        # Clear the old plot
        self.ax.clear()
        self.ax.set_xlim(-1, 1)
        self.ax.set_ylim(-1, 1)
        self.ax.set_aspect("equal")

        # Plot points
        if self.points_inside:
            x_in, y_in = zip(*self.points_inside)
        else:
            x_in, y_in = [], []
        if self.points_outside:
            x_out, y_out = zip(*self.points_outside)
        else:
            x_out, y_out = [], []

        self.ax.scatter(x_in, y_in, color="blue", s=1, label="Inside Circle")
        self.ax.scatter(x_out, y_out, color="red", s=1, label="Outside Circle")

        # Estimate Pi
        if self.total_points > 0:
            pi_estimate = 4.0 * self.inside_circle / self.total_points
        else:
            pi_estimate = 0.0

        self.label_pi.config(text=f"Estimated Pi: {pi_estimate:.6f}")

        # Absolute Error
        abs_error = abs(pi_estimate - math.pi)
        self.label_error.config(text=f"Absolute Error: {abs_error:.6f}")

        # Check convergence (threshold + consecutive hits)
        if abs_error < self.convergence_threshold:
            self.consecutive_hits += 1
        else:
            self.consecutive_hits = 0

        # If we haven't converged yet, but meet the consecutive threshold, we declare convergence
        if not self.converged and self.consecutive_hits >= self.consecutive_needed:
            self.converged = True
            self.convergence_time = time.time() - self.start_time
            # We can compute a time-based score
            self.final_time_score = self.convergence_time

        # Time Elapsed
        elapsed_time = time.time() - self.start_time
        self.label_time.config(text=f"Time Elapsed: {elapsed_time:.2f} s")

        # Memory Usage (current)
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        current_mem_usage_mb = mem_info.rss / (1024 * 1024)
        self.label_mem_current.config(text=f"Current Mem Usage: {current_mem_usage_mb:.2f} MB")

        # Update peak memory usage
        if current_mem_usage_mb > self.peak_mem_usage_mb:
            self.peak_mem_usage_mb = current_mem_usage_mb
        self.label_mem_peak.config(text=f"Peak Mem Usage: {self.peak_mem_usage_mb:.2f} MB")

        # ---------- Scores ----------
        # 1) Time-to-Convergence Score
        if self.final_time_score is not None:
            # Let's color it green if time < 10, otherwise red (arbitrary threshold)
            color_time = "green" if self.final_time_score < 10 else "red"
            self.label_time_score.config(
                text=f"Time-to-Convergence Score: {self.final_time_score:.2f} s",
                fg=color_time
            )
        else:
            self.label_time_score.config(text="Time-to-Convergence Score: N/A", fg="black")

        # 2) Aggregated Score
        # Example formula: aggregated_score = time_to_convergence + (0.01 * peak_mem_usage)
        # or anything else you'd like to factor in
        if self.final_time_score is not None:
            aggregated_score = self.final_time_score + 0.01 * self.peak_mem_usage_mb
            # Color logic, for example if aggregated_score < 10, green, else red
            color_agg = "green" if aggregated_score < 10 else "red"
            self.label_agg_score.config(
                text=f"Aggregated Score: {aggregated_score:.2f}",
                fg=color_agg
            )
        else:
            self.label_agg_score.config(text="Aggregated Score: N/A", fg="black")

        # Redraw the canvas
        self.canvas.draw()

if __name__ == "__main__":
    # Ensure psutil is installed: pip install psutil
    root = tk.Tk()
    app = MonteCarloApp(root)
    root.mainloop()
