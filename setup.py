import os

from setuptools import find_packages, setup

setup(
    name="fontdownloader",
    version="0.2.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "requests",
        "beautifulsoup4",
    ],
    extras_require={
        "dev": [
            "ruff",
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
            "fontdownloader=fontdownloader.cli:main",
        ],
    },
    author="Your Name",
    description="A CLI tool to search and download Google Webfonts",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
)
