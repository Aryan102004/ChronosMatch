from setuptools import setup, Extension
from Cython.Build import cythonize


extensions = [
    Extension(
        "cython_engine.order_book",
        ["cython_engine/order_book.pyx"],
    ),
    Extension(
        "cython_engine.matching_engine",
        ["cython_engine/matching_engine.pyx"],
    ),
]


setup(
    name="chronosmatch-cython",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
        },
    ),
)