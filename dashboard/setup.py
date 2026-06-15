from setuptools import setup, find_packages

setup(
    name="dashboard",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "core",
        "fastapi",
        "uvicorn",
        "jinja2",
    ],
)
