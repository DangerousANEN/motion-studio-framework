from setuptools import find_packages, setup

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="msf",
    version="0.1.0",
    description="Motion Studio Framework - Automated Viral Video Generation Pipeline",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "msf=msf.cli:cli",
        ],
    },
    python_requires=">=3.10",
)
