"""
Setup per installare il server MCP come package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-codebase-server",
    version="0.2.0",
    author="Your Name",
    description="Server MCP per l'analisi e l'indicizzazione del codebase",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "mcp>=1.0.0",
        "pydantic>=2.0.0",
        "aiosqlite>=0.19.0",
        "sentence-transformers>=2.2.0",
        "numpy>=1.24.0",
        "python-dotenv>=1.0.0",
        "chardet>=5.0.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-codebase-server=mcp_server.server:main",
            "mcp-index=mcp_server.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
