import pytest
import monte_carlo  # Your compiled Pybind11 module


def test_monte_carlo_step_std_basic():
    # Test a small case
    num_points = 3798
    num_threads = 99

    points = monte_carlo.monte_carlo_step_std(num_points, num_threads)

    # Check the length
    assert len(points) == num_points, "Expected exactly 100 points returned"

    # Check structure: each item is (float, float, bool)
    x, y, inside = points[0]
    assert isinstance(x, float)
    assert isinstance(y, float)
    assert isinstance(inside, bool)

    # Optional: we can do statistical checks on the ratio inside vs. total
    # For a small sample of 100, it's not guaranteed close to pi, but let's
    # ensure no anomalies like all points are inside or all outside
    inside_count = sum(1 for (_, _, i) in points if i)
    assert 0 < inside_count < num_points


def test_get_available_threads():
    max_threads = monte_carlo.get_available_threads()
    assert max_threads >= 1
