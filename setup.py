import re
from setuptools import setup, find_packages


__version__ = "0.0.33"

with open("README.md", "r") as readme:
    description = readme.read()
    # Patch the relative links to absolute URLs that will work on PyPI.
    description2 = re.sub(
        r']\(([\w/.-]+\.png)\)',
        r'](https://github.com/vivarium-collective/biosimulator-processes/raw/main/\1)',
        description)
    long_description = re.sub(
        r']\(([\w/.-]+)\)',
        r'](https://github.com/vivarium-collective/biosimulator-processes/blob/main/\1)',
        description2)

setup(
    name="biosimulator-processes",
    version=__version__,
    author="Alex Patrie, Eran Agmon, Ryan Spangler",
    author_email=" alexanderpatrie@gmail.com, agmon.eran@gmail.com, ryan.spangler@gmail.com",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vivarium-collective/biosimulator-processes",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "bigraph-schema",
        "process-bigraph",
        "bigraph-builder",
        "bigraph-viz",
        "amici",
        "numpy",
        "pytest",
        "tellurium",
        "copasi-basico",
        "cobra",
        "zarr",
        "termcolor",
        "jupyterlab",
        "notebook",
        "python-libsbml",
        "docker",
        "python-libnuml",
        "seaborn",
        "toml",
        "pyyaml",
        "pydantic",
        "h5py",
        "biosimulators-utils"
    ],
    extras_require={
        "smoldyn": ["smoldyn", "simulariumio"],
    }
)
