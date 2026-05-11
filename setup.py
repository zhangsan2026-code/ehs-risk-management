from setuptools import setup, find_packages

setup(
    name='python_project',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
    ],
    entry_points={
        'console_scripts': [
            'python_project=src.main:main',
        ],
    },
)
