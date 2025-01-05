import pybind11
from setuptools import setup, Extension
# from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Extension(
        "monte_carlo",
        ["src/monte_carlo.cpp"],
        include_dirs=[pybind11.get_include()],
        language='c++'
    ),
]

setup(
    name='monte_carlo',
    version='0.1',
    ext_modules=ext_modules,
)
