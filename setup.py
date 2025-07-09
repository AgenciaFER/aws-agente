from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="aws-multi-account-agent",
    version="1.0.0",
    author="AWS Multi-Account Agent Team",
    author_email="team@aws-agent.com",
    description="Agente AWS para gerenciamento de múltiplas contas com credenciais seguras",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/aws-multi-account-agent",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
            "myst-parser>=2.0.0",
        ],
        "analytics": [
            "pandas>=2.0.0",
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aws-agent=aws_agent.cli.main:main",
            "aws-multi-agent=aws_agent.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "aws_agent": [
            "templates/*.yaml",
            "templates/*.json",
            "config/*.yaml",
            "config/*.json",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/your-org/aws-multi-account-agent/issues",
        "Source": "https://github.com/your-org/aws-multi-account-agent",
        "Documentation": "https://aws-multi-account-agent.readthedocs.io/",
    },
)
