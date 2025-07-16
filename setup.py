#!/usr/bin/env python3
"""
AI Agent System for Code Auditing
Setup configuration for package installation
"""

from setuptools import setup, find_packages
import os

# Read long description from README
def read_readme():
    if os.path.exists('README.md'):
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    return "AI Agent System for automated code auditing and analysis"

# Read requirements
def read_requirements():
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="ai-code-audit-agents",
    version="1.0.0",
    description="AI Agent System for automated code auditing and analysis",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="AI Code Audit Team",
    author_email="team@ai-code-audit.com",
    url="https://github.com/your-org/ai-code-audit-agents",
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    python_requires='>=3.9',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Bug Tracking",
    ],
    entry_points={
        'console_scripts': [
            'ai-audit=console.main:main',
            'ai-audit-web=web.server:main',
            'ai-audit-agent=agents.runner:main',
        ],
    },
)