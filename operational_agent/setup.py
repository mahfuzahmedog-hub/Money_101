from setuptools import setup, find_packages

setup(
    name="operational_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "core",
        "llm_router",
        "browser-use",
        "playwright",
        "cryptography",
    ],
)
