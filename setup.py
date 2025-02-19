from setuptools import setup, find_packages

VERSION = "0.3.19"

setup(
    name="biosimulator-processes",
    version=VERSION,
    description="Core implementations of process-bigraph.composite.Process aligning with BioSimulators simulator tools.",
    author="Alex Patrie",
    author_email="alexanderpatrie@gmail.com",
    packages=find_packages(),
    install_requires=[
        "process-bigraph",
        "pip-autoremove",
        "seaborn",
        "ipython",
        "toml",
        "pyyaml",
        "python-dotenv",
        "requests",
        "h5py",
        "python-libsbml"
    ],
    # extras_require={
    #     "amici": ["amici"],
    #     "builder": ["bigraph-builder", "bigraph-viz"],
    #     "cobra": ["cobra", "imageio"],
    #     "copasi": ["copasi-basico"],
    #     "dev": ["flake8", "mypy", "pip-autoremove", "pytest"],
    #     "quantum": ["qiskit", "qiskit-ibm-runtime", "qiskit-nature", "pyscf"],
    #     "smoldyn": ["smoldyn", "simulariumio"],
    #     "tellurium": ["tellurium", "libroadrunner"],
    # },
    python_requires=">=3.10"
)
