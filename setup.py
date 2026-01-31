"""
Setup configuration for Intelligent Form Agent package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="intelligent-form-agent",
    version="1.0.0",
    author="Intelligent Form Agent Team",
    author_email="team@example.com",
    description="An AI-powered system for processing, understanding, and analyzing forms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/intelligent-form-agent",
    packages=find_packages(exclude=["tests", "tests.*", "notebooks"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: General",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pdfplumber>=0.10.0",
        "pypdf>=3.0.0",
        "Pillow>=10.0.0",
        "pytesseract>=0.3.10",
        "pdf2image>=1.16.0",
        "sentence-transformers>=2.2.0",
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "pandas>=2.0.0",
        "python-dateutil>=2.8.0",
        "pyyaml>=6.0.0",
        "tqdm>=4.66.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
        ],
        "ui": [
            "streamlit>=1.28.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "form-agent=src.agent:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json"],
    },
)
