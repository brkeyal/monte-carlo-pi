# monte-carlo-pi
A Monte Carlo Pi Estimation project, featuring a C++ multihreaded service (via Pybind11) and a Python (Tkinter) GUI for real-time visualization and performance monitoring

```markdown
# Monte Carlo Pi Estimation (C++ + Python)

This project demonstrates a Monte Carlo approach to estimating \\(\pi\\) by randomly sampling points in a 2D plane and checking how many fall inside a unit circle. The core logic is written in **C++** (exposed to Python via **Pybind11**), and a **Python Tkinter** GUI provides real-time visualization and performance monitoring.

## Features

1. **C++ Implementation**
   - Uses `std::thread` (or optionally OpenMP) for **multithreading**.  
   - Returns a batch of \\((x, y, inside)\\) tuples to Python.  
   - Thread-local random number generation for consistent parallel results.

2. **Python Tkinter GUI**  
   - **Batch size** and **thread count** can be set by the user.  
   - **Real-time plotting** via `matplotlib`, showing inside/outside points.  
   - **Performance KPIs**: time elapsed, memory usage (current & peak), convergence checks (\\(\pm 10^{-4}\\) threshold), and an aggregated score once convergence is reached.

3. **Automated Tests**  
   - **Pytest** tests to verify:
     - C++ module calls and returned data.
     - Python logic for setting and parsing batch size / thread count.
     - (Optional) basic GUI tests.

4. **Continuous Integration**  
   - GitHub Actions workflow (`.github/workflows/ci.yml`) to:
     - Build the Pybind11 extension in-place.
     - Run tests automatically on commits and pull requests.

## Project Structure

```
.
├─ monte_carlo.cpp        # Main C++ file with Monte Carlo + threading logic
├─ setup.py               # Pybind11 build script
├─ main.py                # Python Tkinter GUI + logic
├─ tests/
│  ├─ test_monte_carlo.py # Example Pytest for C++ logic & Python integration
│  └─ ...
├─ requirements.txt       # (Optional) Python dependencies
└─ .github/workflows/ci.yml # GitHub Actions workflow
```

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/monte-carlo-pi.git
cd monte-carlo-pi
```
*(Or create your repo in PyCharm and push there—see below for details on using PyCharm.)*

### 2. Build the C++ Extension

```bash
python setup.py build_ext --inplace
```

This will compile the Pybind11 extension (`monte_carlo.*`).

### 3. Install Dependencies

If you have a `requirements.txt`, run:

```bash
pip install -r requirements.txt
```

Otherwise, you’ll need at least:
- **pybind11** (for building the extension)
- **pytest** (for testing)
- **matplotlib** (for plotting in the GUI)
- **psutil** (for memory usage)
- **tkinter** (usually included with Python on most OSes, or install `python3-tk` on Linux)

### 4. Run the GUI

```bash
python main.py
```

A Tkinter window should appear, allowing you to:
- **Start/Stop** the simulation.
- Modify **Batch Size** (points per step).
- Modify **Thread Count** (for multithreading).
- See a **real-time** scatter plot of inside/outside points, along with metrics like **estimated \\(\pi\\)**, **time elapsed**, **memory usage**, **time-to-convergence**, etc.

### 5. Test the Project

```bash
pytest tests/
```

This runs the unit tests (e.g., verifying the C++ module’s return values, checking Python logic, etc.).

## Using PyCharm

1. **Open** the project in PyCharm.
2. **Enable Git** (if not already): `VCS > Enable Version Control Integration`.
3. **Commit** your changes locally.
4. **Share** the project on GitHub: `VCS > Import into Version Control > Share Project on GitHub`.
5. **Build & Test**:  
   - Use PyCharm’s built-in terminal or “Run” configurations to run `python setup.py build_ext --inplace`.  
   - Use PyCharm’s “Run” or “Debug” for `main.py`.  
   - Use PyCharm’s “Python tests” run configuration for `pytest`.

## Continuous Integration (GitHub Actions)

A `.github/workflows/ci.yml` file is included to:
- Set up Python
- Install dependencies
- Build the Pybind11 extension
- Run `pytest`

Whenever you push code or open a pull request, GitHub Actions will build and test your code automatically.

## Contributing

1. **Fork** the repo, make changes, and open a **Pull Request**.
2. Submit **issues** for bugs or new feature ideas.
3. We welcome improvements to parallelization, plotting, or advanced performance metrics.

## License

*(Include your chosen license here, e.g., MIT, BSD, or Apache 2.0.)*

```
