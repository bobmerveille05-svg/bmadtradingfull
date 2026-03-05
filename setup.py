from __future__ import annotations

from setuptools import find_packages, setup


setup(
    name="bmad-trading-system",
    version="0.1.0",
    description="BMAD Trading System orchestrator and agent framework",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10",
    install_requires=[
        "pydantic>=2.6,<3",
        "typer>=0.12,<1",
        "jinja2>=3.1,<4",
    ],
    extras_require={
        "dev": [
            "pytest>=8,<9",
            "hypothesis>=6,<7",
        ]
    },
    entry_points={"console_scripts": ["bmadts=bmadts.__main__:main"]},
)
