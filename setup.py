from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='kaiserlift',
    version='0.1.2',
    description='Data-driven progressive overload',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Douglas Kaiser',
    author_email='douglastkaiser@gmail.com',
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'kaiserlift-cli = kaiserlift.main:main',
        ],
    },
)
