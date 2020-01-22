from setuptools import setup

setup(
    setup_requires=["wheel >= 0.32", "pytest-runner >= 5.0, <6.0"],
    entry_points={"pytest11": ["docker = pytest_docker"]},
)
