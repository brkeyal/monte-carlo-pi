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

std::vector<std::tuple<double, double, bool>> monte_carlo_step_std(int num_points, int num_threads) {
    if (g_known_num_threads != num_threads || g_known_num_points != num_points) {
        std::printf("EYALBTEST monte_carlo_step_std num_points=%d num_threads=%d\n", num_points, num_threads);
        g_known_num_threads = num_threads;
        g_known_num_points = num_points;
    }

    // We will store all the points here.
    // Each thread will write to a different sub-range, so no locking is needed.
    std::vector<std::tuple<double, double, bool>> points(num_points);

    // If num_threads <= 0 or 1, just do single-threaded
    if (num_threads < 1) {
        num_threads = 1;
    }
    // If num_threads > num_points, no point in having more threads than points
    if (num_threads > num_points) {
        num_threads = num_points;
    }

    // Lambda that each thread will run:
    auto worker = [&](int start_idx, int end_idx) {
        // Create a thread-local random engine + distribution
        // Using std::random_device for a seed, then a Mersenne Twister
        std::random_device rd;
        std::mt19937 gen(rd());  // or seed with a fixed value for reproducibility
        std::uniform_real_distribution<double> dist(-1.0, 1.0);

        for (int i = start_idx; i < end_idx; ++i) {
            double x = dist(gen);
            double y = dist(gen);
            bool inside_circle = (x * x + y * y <= 1.0);
            points[i] = std::make_tuple(x, y, inside_circle);
        }
    };

    // We'll divide num_points among num_threads as evenly as possible
    std::vector<std::thread> threads;
    threads.reserve(num_threads);

    int chunk_size = num_points / num_threads;
    int remainder = num_points % num_threads;

    int start = 0;
    for (int t = 0; t < num_threads; ++t) {
        // Each thread gets chunk_size points, plus 1 extra if remainder > 0
        int this_chunk = chunk_size + (t < remainder ? 1 : 0);
        int end = start + this_chunk;
        threads.emplace_back(worker, start, end);
        start = end;
    }

    // Join all threads
    for (auto &th : threads) {
        th.join();
    }

    return points;
}

int get_available_threads() {
    std::cout << "EYALBTEST GOT to get_available_threads\n";
    // hardware_concurrency() returns an unsigned int, or 0 if not well defined.
    unsigned int n = std::thread::hardware_concurrency();
    // If 0, we fallback to 1 (at least one thread).
    return (n == 0) ? 1 : static_cast<int>(n);
}

PYBIND11_MODULE(monte_carlo, m) {
    m.doc() = "Monte Carlo Pi - pure std::thread parallel version";
    m.def("monte_carlo_step_std", &monte_carlo_step_std,
          "Perform a Monte Carlo step using only std::thread parallelism");
    m.def("get_available_threads", &get_available_threads,
          "Return the number of hardware concurrency (logical cores) as reported by std::thread.");
}
