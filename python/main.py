import threading
import time
import math
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import utils

import os
import psutil

# Import your Pybind11-compiled C++ module, which supports multi-threading via OpenMP
import monte_carlo

MAX_POINTS_TO_PLOT = 1000
# MAX_PLOT_DURATION = 1/60  # ~0.0167 seconds
MAX_PLOT_DURATION = 0.1 # seconds
CONVERGENCE_THRESHOLD = 1e-3  # TODO: change back to -4
CONSECUTIVE_NEEDED = 1000  # must meet threshold consecutive times # TODO: optimize

# # Setup
# plot_widget = pg.PlotWidget()
# plot_inside = plot_widget.plot([], [], pen=None, symbol='o', symbolBrush='b')
# plot_outside = plot_widget.plot([], [], pen=None, symbol='o', symbolBrush='r')


class MonteCarloApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monte Carlo Pi Estimation - Performance Demo")

        # ---------------
        # USER CONTROLS
        # ---------------
        self.running = False
        self.during_simulation = False
        self.batch_size = 1000      # default batch size
        self.num_threads = 2        # default number of threads
        self.simulation_report = None

        # ---------------
        # SIM STATS
        # ---------------
        self.total_points = 0
        self.inside_circle = 0
        self.start_time = None

        # Track points (for plotting)
        self.points_inside_to_plot = []
        self.points_outside_to_plot = []

        # ---------------
        # CONVERGENCE / SCORE
        # ---------------
        self.consecutive_hits = 0
        self.converged = False
        self.convergence_time = None
        self.aggregated_score = None
        self.points_per_second = None

        # We'll track peak memory usage
        self.peak_mem_usage_mb = 0.0

        # We'll display two scores:
        # 1) Time-to-Convergence (once stable)
        # 2) Aggregated Score (based on more factors)
        # self.final_time_score = None
        # self.final_agg_score = None

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

        # Simulate Button
        self.simulate_button = tk.Button(control_frame, text="Simulation", command=self.simulate)
        self.simulate_button.pack(side=tk.BOTTOM, padx=5)

        # Start/Stop Button
        self.button = tk.Button(control_frame, text="Start", command=self.on_main_button_pressed)
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

        # Show efficiency metric (points_per_seconds)
        self.label_points_per_seconds = tk.Label(root, text="Points per Second: 0")
        self.label_points_per_seconds.pack()

        # Show time score (time-to-convergence) once stable
        self.label_time_score = tk.Label(root, text="Time-to-Convergence Score: N/A", fg="black")
        self.label_time_score.pack()

        # Show aggregated score
        self.label_agg_score = tk.Label(root, text="Aggregated Score: N/A", fg="black")
        self.label_agg_score.pack()

    def on_main_button_pressed(self):
        if self.running and self.during_simulation:
            # Stopped button was pressed. stop simulation, if running
            self.during_simulation = False

        if not self.running:
            # Start was pressed - remove simulation report, if exists
            if self.simulation_report is not None:
                self.simulation_report.destroy()
                self.simulation_report = None  # Reset the reference

        self.toggle_simulation()

    def toggle_simulation(self):
        if self.running:

            # Stopping
            self.running = False
            self.button.config(text="Start")
            self.simulate_button.config(state='normal')  # Disable the button
            self.batch_entry.config(state='normal')
            self.thread_entry.config(state='normal')
        else:
            # Starting
            self.running = True
            self.button.config(text="Stop")
            self.simulate_button.config(state='disabled')  # Disable the button
            self.batch_entry.config(state='disabled')
            self.thread_entry.config(state='disabled')
            self.button.focus() # clear any selection or text fields marker, if exists afte editing them

            # Read user inputs
            try:
                self.batch_size = int(self.batch_entry.get())
            except ValueError:
                self.batch_size = 1000

            try:
                self.num_threads = int(self.thread_entry.get())
            except ValueError:
                self.num_threads = 2

            # Reset stats
            self.total_points = 0
            self.inside_circle = 0
            self.points_inside_to_plot.clear()
            self.points_outside_to_plot.clear()

            self.converged = False
            self.convergence_time = None
            self.aggregated_score = None
            self.points_per_second = None
            self.consecutive_hits = 0
            self.peak_mem_usage_mb = 0.0

            # self.final_time_score = None
            # self.final_agg_score = None

            self.start_time = time.time()

            # Kick off in a separate thread
            threading.Thread(target=self.run_simulation, daemon=True).start()

    def run_simulation(self):

        monte_carlo.set_threads(self.num_threads)

        """ Continuously run simulation while self.running is True. """
        while self.running:
            # Generate a batch of random points from C++
            # points = monte_carlo.monte_carlo_step_std(num_points=10000, num_threads=4)
            points = monte_carlo.monte_carlo_step_std(self.batch_size, self.num_threads)

            # print(f"EYALBTEST points size = {len(points)}")
            # print(f"EYALBTEST points_inside size = {len(self.points_inside_to_plot)}")
            # print(f"EYALBTEST points_outside size = {len(self.points_outside_to_plot)}")

            for x, y, inside in points:
                if inside:
                    # if (x, y) not in self.points_inside:
                        self.points_inside_to_plot.append((x, y))
                        if len(self.points_inside_to_plot) > MAX_POINTS_TO_PLOT:
                            self.points_inside_to_plot.pop(0)
                        self.inside_circle += 1
                else:
                    # if (x, y) not in self.points_outside:
                        self.points_outside_to_plot.append((x, y))
                        if len(self.points_outside_to_plot) > MAX_POINTS_TO_PLOT:
                            self.points_outside_to_plot.pop(0)
                self.total_points += 1

            # Before plotting
            plotting_start_time = time.time()

            # Update the UI (plots + KPIs)
            self.update_plot()

            # After plotting
            plotting_end_time = time.time()
            plotting_duration = plotting_end_time - plotting_start_time
            # print(f"Plotting took {plot_duration:.4f} seconds")

            if plotting_duration > MAX_PLOT_DURATION:
                print(f"Warning: Plotting took {plotting_duration:.4f} seconds, which exceeds max threshold.")
                # Optionally, raise exception

            # Optional short sleep if you want to limit CPU usage or UI updates
            # time.sleep(0.01)

    def draw_plot(self):
        # Clear the old plot
        self.ax.clear()
        self.ax.set_xlim(-1, 1)
        self.ax.set_ylim(-1, 1)
        self.ax.set_aspect("equal")

        # Plot points
        if self.points_inside_to_plot:
            x_in, y_in = zip(*self.points_inside_to_plot)
        else:
            x_in, y_in = [], []
        if self.points_outside_to_plot:
            x_out, y_out = zip(*self.points_outside_to_plot)
        else:
            x_out, y_out = [], []

        self.ax.scatter(x_in, y_in, color="blue", s=1, label="Inside Circle")
        self.ax.scatter(x_out, y_out, color="red", s=1, label="Outside Circle")

        # Redraw the canvas
        self.canvas.draw()

    def update_plot(self):
        """ Update the plot and the KPI labels. """

        self.draw_plot()

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
        if abs_error < CONVERGENCE_THRESHOLD:
            self.consecutive_hits += 1
        else:
            self.consecutive_hits = 0

        # Time Elapsed
        elapsed_time = time.time() - self.start_time
        self.label_time.config(text=f"Time Elapsed: {elapsed_time:.2f} s")

        # Memory Usage (current)
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info() # psutil.virtual_memory().used / (1024 * 1024)
        current_mem_usage_mb = mem_info.rss / (1024 * 1024)
        self.label_mem_current.config(text=f"Current Mem Usage: {current_mem_usage_mb:.2f} MB")

        # Update peak memory usage
        if current_mem_usage_mb > self.peak_mem_usage_mb:
            self.peak_mem_usage_mb = current_mem_usage_mb
        self.label_mem_peak.config(text=f"Peak Mem Usage: {self.peak_mem_usage_mb:.2f} MB")

        # Update points per second
        actual_elapsed = time.time() - self.start_time
        # print(f"EYALBBBBTIME Elapsed time {actual_elapsed:.2f}")
        self.points_per_second = self.total_points / actual_elapsed  # self.batch_size * self.num_threads
        self.label_points_per_seconds.config(text=f"Points per second: {utils.format_number(self.points_per_second)}")
        # print(f"EYALBBBBTIME points_per_second {utils.format_number(points_per_second)}")

        # If we haven't converged yet, but meet the consecutive threshold, we declare convergence
        if not self.converged and self.consecutive_hits >= CONSECUTIVE_NEEDED:
            self.converged = True
            self.convergence_time = time.time() - self.start_time
            # We can compute a time-based score
            # self.final_time_score = self.convergence_time

            # ---------- Scores ----------
            # 1) Time-to-Convergence Score
            # Let's color it green if time < 10, otherwise red (arbitrary threshold)
            color_time = "green" if self.convergence_time < 10 else "red"
            self.label_time_score.config(
                text=f"Time-to-Convergence Score: {self.convergence_time:.2f} s",
                fg=color_time
            )

            # 2) Aggregated Score
            # Example formula: aggregated_score = time_to_convergence + (0.01 * peak_mem_usage)
            # or anything else you'd like to factor in
            self.aggregated_score = self.convergence_time + 0.01 * self.peak_mem_usage_mb
            # Color logic, for example if aggregated_score < 10, green, else red
            color_agg = "green" if self.aggregated_score < 10 else "red"
            self.label_agg_score.config(
                text=f"Aggregated Score: {self.aggregated_score:.2f}",
                fg=color_agg
            )

        if self.convergence_time is None:
            self.label_time_score.config(text="Time-to-Convergence Score: N/A", fg="black")
            self.label_agg_score.config(text="Aggregated Score: N/A", fg="black")

        else:
            # Running completed
            self.toggle_simulation()

    def simulate(self):
        print("Simulate button clicked")
        """Simulate with multiple configurations to find the optimal parameters."""
        # Arrays of batch sizes and thread counts to test
        #batch_sizes = [100, 500, 1000, 5000, 10000, 50000, 100000]
        batch_sizes = [1000, 10000, 50000, 100000, 500000, 1000000]
        thread_counts = [1, 2, 4, 8, 12]
        runs =  3 # Run each configuration multiple times

        self.during_simulation = True

        # Clear previous results
        # self.simulation_results = []
        if self.simulation_report is None or not self.simulation_report.winfo_exists():
            self.simulation_report = tk.Text(self.root, height=10, width=80)
            self.simulation_report.pack(pady=10)
            self.simulation_report.delete(1.0, tk.END)
        else:
            self.simulation_report.delete(1.0, tk.END)

        #self.simulate_button.config(state='disabled')  # Disable the button
        # Iterate over batch sizes and thread counts
        for batch_size in batch_sizes:
            for num_threads in thread_counts:
                for _ in range(runs):


                    self.batch_entry.delete(0, 'end')  # Clear existing content
                    self.batch_entry.insert(0, str(batch_size))

                    self.thread_entry.delete(0, 'end')  # Clear existing content
                    self.thread_entry.insert(0, str(num_threads))

                    self.toggle_simulation()

                    # Wait until simulation is done
                    #while not self.simulation_done:
                    while self.running:
                        self.root.update()  # Keep the GUI responsive

                    if not self.during_simulation:
                        print("Simulation stopped by user.")
                        stopped = True
                        break
                    else:
                        # we got here because a run was succesfully ended. insert results
                        summary = f"Batch: {batch_size}, Threads: {num_threads}, Time: {self.convergence_time:.2f}s, "\
                                  f"PPS: {utils.format_number(self.points_per_second)}, Score: {self.aggregated_score:.2f}\n"
                        self.simulation_report.insert(tk.END, summary)
                        print(summary)
                if not self.during_simulation:
                    break
            if not self.during_simulation:
                break

if __name__ == "__main__":
    # Ensure psutil is installed: pip install psutil
    root = tk.Tk()
    app = MonteCarloApp(root)
    root.mainloop()
