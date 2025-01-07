#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <thread>
#include <vector>
#include <tuple>
#include <random>
#include <cmath>
#include <iostream>

namespace py = pybind11;

int g_known_num_threads = -1;
int g_known_num_points = -1;
std::vector<std::thread> g_threads; // Global thread pool

// Worker lambda function for threads
auto g_worker = [](int start_idx, int end_idx, std::vector<std::tuple<double, double, bool>> &points) {
    // Create a thread-local random engine + distribution
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<double> dist(-1.0, 1.0);

    for (int i = start_idx; i < end_idx; ++i) {
        double x = dist(gen);
        double y = dist(gen);
        bool inside_circle = (x * x + y * y <= 1.0);
        points[i] = std::make_tuple(x, y, inside_circle);
    }
};

// Initialize threads once
void set_threads(int num_threads) {
    if (g_known_num_threads == num_threads) {
        std::cout << "Threads already initialized with num_threads=" << num_threads << std::endl;
        return;
    }

    std::cout << "Initializing threads with num_threads=" << num_threads << std::endl;
    g_known_num_threads = num_threads;
    g_threads.clear(); // Clear existing threads

    // Reserve threads for later use
    g_threads.reserve(num_threads);
}

// Monte Carlo step function
std::vector<std::tuple<double, double, bool>> monte_carlo_step_std(int num_points, int num_threads) {
    if (g_known_num_threads != num_threads) {
        set_threads(num_threads);
    }

    // Allocate points vector
    std::vector<std::tuple<double, double, bool>> points(num_points);

    // Adjust thread count if necessary
    if (num_threads < 1) {
        num_threads = 1;
    }
    if (num_threads > num_points) {
        num_threads = num_points; // TODO: don't allow / re-set threads
    }

    // Divide work among threads
    int chunk_size = num_points / num_threads;
    int remainder = num_points % num_threads;

    int start = 0;
    for (int t = 0; t < num_threads; ++t) {
        int this_chunk = chunk_size + (t < remainder ? 1 : 0);
        int end = start + this_chunk;

        if (t >= g_threads.size()) {
            g_threads.emplace_back(g_worker, start, end, std::ref(points));
        } else {
            g_threads[t] = std::thread(g_worker, start, end, std::ref(points));
        }

        start = end;
    }

    // Join threads
    for (auto &th : g_threads) {
        if (th.joinable()) {
            th.join();
        }
    }

    return points;
}

// Get available threads
int get_available_threads() {
    std::cout << "EYALBTEST GOT to get_available_threads\n";
    unsigned int n = std::thread::hardware_concurrency();
    return (n == 0) ? 1 : static_cast<int>(n);
}

// TODO: clear threads at the end (or refactor to class)

// Python module
PYBIND11_MODULE(monte_carlo, m) {
    m.doc() = "Monte Carlo Pi - pure std::thread parallel version with persistent threads";
    m.def("set_threads", &set_threads, "Initialize threads once for reuse");
    m.def("monte_carlo_step_std", &monte_carlo_step_std,
          "Perform a Monte Carlo step using pre-initialized threads");
    m.def("get_available_threads", &get_available_threads,
          "Return the number of hardware concurrency (logical cores) as reported by std::thread.");
}
