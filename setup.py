#!/usr/bin/env python3
"""
Setup script for mcp-jira.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-jira",
    version="0.1.0",
    author="Warzuponus",
    description="Model Context Protocol server for Jira with project management capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/warzuponus/mcp-jira",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "mcp>=1.0.0",
        "jira>=3.5.1",
        "python-dotenv>=0.19.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "aiohttp>=3.8.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-jira=mcp_jira.simple_mcp_server:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 