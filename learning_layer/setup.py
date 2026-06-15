from setuptools import setup, find_packages

setup(
    name="learning_layer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["core", "sentence-transformers", "scikit-learn"],
)
