"""
Setup script for Exa MCP Server
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="exa-mcp-server",
    version="1.0.0",
    author="Klavis AI Contributor",
    description="Model Context Protocol server for Exa AI-powered search integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Klavis-AI/klavis",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "exa-mcp-server=src.main:main",
        ],
    },
    keywords="mcp, exa, search, ai, neural-search, model-context-protocol",
    project_urls={
        "Bug Reports": "https://github.com/Klavis-AI/klavis/issues",
        "Source": "https://github.com/Klavis-AI/klavis",
        "Documentation": "https://github.com/Klavis-AI/klavis/blob/main/servers/exa/README.md",
    },
)