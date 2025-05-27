from setuptools import setup, find_packages

setup(
    name='kaiserlift',
    version='0.1.1',
    description='Data-driven progressive overload',
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
