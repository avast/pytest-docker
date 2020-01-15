from sys import exit
from setuptools import setup, version


if version.__version__ < "40.1.0":
    exit(
        "At least version 40.1.0 of setuptools is required ({} is installed)".format(
            version.__version__
        )
    )

setup(
    setup_requires=["wheel >= 0.32", "pytest-runner >= 5.0, <6.0"],
    entry_points={"pytest11": ["docker = pytest_docker"]},
)
