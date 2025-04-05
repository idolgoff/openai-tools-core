"""Setup script for the ai_tools_core package."""
from setuptools import setup, find_packages

setup(
    name="ai_tools_core",
    version="0.4.0",
    description="Core library for AI tools and integrations",
    author="idolgoff",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "python-dotenv>=1.0.0",
        "openai>=1.12.0",
        "colorlog>=6.7.0",
        "pydantic>=2.5.2",
        "tiktoken>=0.5.2",
        "watchdog>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-mock>=3.10.0",
        ],
        "telegram": [
            "python-telegram-bot>=20.0",
        ],
        "test": ["pytest", "pytest-cov"],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    entry_points={
        "console_scripts": [
            "ai-tools=ai_tools_core.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
