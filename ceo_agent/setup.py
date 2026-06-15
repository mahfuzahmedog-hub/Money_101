from setuptools import setup, find_packages

setup(
    name="ceo_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["core", "llm_router"],
)
