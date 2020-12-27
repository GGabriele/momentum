"""setup.py file."""
from setuptools import setup, find_packages

with open("requirements.txt", "r") as fs:
    reqs = [r for r in fs.read().splitlines() if (len(r) > 0 and not r.startswith("#"))]


setup(
    name="momentum",
    version="0.0.0",
    packages=find_packages(exclude=("test*",)),
    author="Gabriele Gerbino",
    author_email="gabrielegerbino@gmail.com>",
    description="Momentum strategy tooling",
    classifiers=[
        "Topic :: Utilities",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
    url="https://github.com/GGabriele/momentum",
    include_package_data=True,
    install_requires=reqs,
    entry_points={
        "console_scripts": [
            "momentum=momentum.main:run",
        ]
    },
)
