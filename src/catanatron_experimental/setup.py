"""
Module: 2. Training Pipeline
Author: Forked
Date: 2026-02-27
Purpose: Implements the setup module for experimental training or agent-development workflows related to the project's learning pipeline.
"""

import setuptools

setuptools.setup(
    name="catanatron_experimental",
    version="1.0.0",
    author="Bryan Collazo",
    author_email="bcollazo2010@gmail.com",
    description="Experimental scripts",
    url="https://github.com/bcollazo/catanatron",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "catanatron[web,gym]",
        "tensorflow",
    ],  # careful including heavy ml-libs since might break heroku build
)
