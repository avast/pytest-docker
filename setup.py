from setuptools import setup

setup(
    setup_requires=["wheel >= 0.32"],
    entry_points={"pytest11": ["docker = pytest_docker"]},
)
