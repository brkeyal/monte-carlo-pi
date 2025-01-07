# Monte Carlo Pi Estimation (C++ + Python)

This project demonstrates a Monte Carlo approach to estimating π by randomly sampling points in a 2D plane and checking how many fall inside a unit circle. The core logic is written in C++ (exposed to Python via Pybind11), and a Python Tkinter GUI provides real-time visualization and performance monitoring.

## Features

1. C++ Implementation
   - Uses `std::thread` for multithreading
   - Returns a batch of (x, y, inside) tuples to Python
   - Thread-local random number generation for consistent parallel results

2. Python Tkinter GUI
   - Batch size and thread count can be set by the user
   - Real-time plotting via matplotlib, showing inside/outside points
   - Performance KPIs: time elapsed, memory usage (current & peak), convergence checks (±10^-4 threshold), and an aggregated score once convergence is reached
   - Simulation mode for optimizing batch size and thread count values

3. Automated Tests
   - Pytest tests to verify:
     - C++ module calls and returned data
     - Python logic for setting and parsing batch size / thread count
     - Optional GUI tests

4. Continuous Integration
   - GitHub Actions workflow to:
   - Build the Pybind11 extension in-place
   - Run tests automatically on commits and pull requests

5. Further Improvements TODO:
   - Improve performance metrics (cpu usage, total memory, etc) and calculate relevant score (normalized)
   - Further optimization in C++ code
      - optimize threads handling / threads pool
      - move creation of random engines outside of loop
   - Improve/enhance the python gui rendering
   - Some tech debts/best practices - avoid global params / refactor to class / clear vector on termination, etc
   - Add more testing

  

## Project Structure
```
monte-carlo-pi/
│
├── src/
│   ├── monte_carlo.cpp     # Main C++ file with Monte Carlo + threading logic
│   └── setup.py           # Pybind11 build script
│
├── python/
│   ├── main.py            # Python Tkinter GUI + logic
│   └── utils/             # Helper functions and utilities
│
├── tests/
│   ├── test_monte_carlo.py
│   └── test_gui.py
│
├── requirements.txt       # Python dependencies
├── README.md
└── .github/
    └── workflows/
        └── ci.yml        # GitHub Actions workflow
```

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/brkeyal/monte-carlo-pi.git
cd monte-carlo-pi
```
### 2. Install Requirements
```bash
pip install -r requirements.txt

# If that doesn't work, try:
pip3 install -r requirements.txt

# If that doesn't work, try:
python -m pip install -r requirements.txt
```

### 3. Build the C++ Extension
```bash
python src/setup.py build_ext --inplace
```

### 4. Set Python path to include the source directory:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)  # On Windows, use: set PYTHONPATH=%PYTHONPATH%;%cd%
```

### 5. Run the GUI
```bash
python python/main.py
```

The GUI provides:
- Start/Stop controllers
- Simluator controller
- Batch Size adjustment
- Thread Count selection
- Real-time visualization
- Performance metrics display

### 5. Run Tests
```bash
pytest tests/
```

## Development with PyCharm

1. Open project in PyCharm
2. Enable Version Control: VCS > Enable Version Control Integration
3. Build the extension: Run `python setup.py build_ext --inplace` in terminal
4. Run the GUI: Execute `main.py`
5. Run tests: Configure Python tests in PyCharm

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Acknowledgments

- Contributors and maintainers
- Pybind11 team for C++/Python bindings
- Python and C++ communities

---
*Note: This project is under active development. Issues and pull requests are welcome.*
