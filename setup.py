from setuptools import setup, find_packages

VERSION = "0.3.9"

setup(
    name="biosimulator-processes",
    version=VERSION,
    description="Core implementations of process-bigraph.composite.Process aligning with BioSimulators simulator tools.",
    author="Alex Patrie",
    author_email="alexanderpatrie@gmail.com",
    packages=find_packages(),
    install_requires=[
        "requests>=2.32.3",
        "h5py>=3.12.1",
        "seaborn>=0.13.2",
        "python-libsbml",
        "process-bigraph>=0.0.23",
        "pip-autoremove",
        "seaborn>=0.13.2",
        "ipython>=8.31.0",
        "toml>=0.10.2",
        "pyyaml>=6.0.2",
        "python-dotenv>=1.0.1",
        "requests>=2.32.3",
        "h5py>=3.12.1",
        "python-libsbml>=5.20.4"
    ],
    extras_require={
        "amici": ["amici"],
        "builder": ["bigraph-builder", "bigraph-viz"],
        "cobra": ["cobra", "imageio"],
        "copasi": ["copasi-basico"],
        "dev": ["flake8", "mypy", "pip-autoremove", "pytest"],
        "quantum": ["qiskit", "qiskit-ibm-runtime", "qiskit-nature", "pyscf"],
        "smoldyn": ["smoldyn", "simulariumio"],
        "tellurium": ["tellurium", "libroadrunner"],
    },
    python_requires=">=3.10"
)
