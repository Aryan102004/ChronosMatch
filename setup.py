from setuptools import setup, Extension
from Cython.Build import cythonize


extensions = [
    Extension(
        "cython_engine.order_book",
        ["cython_engine/order_book.pyx"],
    )
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