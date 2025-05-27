from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
long_description = long_description.replace(
    "](images/", "](https://github.com/douglastkaiser/kaiserlift/raw/main/images/"
)

setup(
    name="kaiserlift",
    version="0.1.4",
    description="Data-driven progressive overload",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Douglas Kaiser",
    author_email="douglastkaiser@gmail.com",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.0.0",
        "numpy>=2.2.6",
        "matplotlib>=3.10.3",
    ],
    entry_points={
        "console_scripts": [
            "kaiserlift-cli = kaiserlift.main:main",
        ],
    },
)
