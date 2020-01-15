Docker-based integration tests
=====
[![PyPI version](https://img.shields.io/pypi/v/pytest-docker?color=blue)](https://pypi.org/project/pytest-docker/)
[![Python versions](https://img.shields.io/pypi/pyversions/pytest-docker)](https://pypi.org/project/pytest-docker/)
[![Code style](https://img.shields.io/badge/formatted%20with-black-black)](https://github.com/psf/black)


# Description
Simple [pytest](http://doc.pytest.org/) fixtures that help you write integration
tests with Docker and [docker-compose](https://docs.docker.com/compose/).
Specify all necessary containers in a `docker-compose.yml` file and and
`pytest-docker` will spin them up for the duration of your tests.

This package is tested with Python versions `3.5`, `3.6`, `3.7` and `3.8` and
`pytest` version 5. Python 2 is not supported.


# Usage
Here is a basic example a test that depends on a service that
responds over HTTP:

```python
import pytest
import requests

from requests.exceptions import ConnectionError


def is_responsive(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except ConnectionError:
        return False


@pytest.fixture(scope="session")
def http_service(docker_ip, docker_services):
    """Ensure that HTTP service is up and responsive."""

    port = docker_services.port_for("abc", 123)
    url = "http://{}:{}".format(docker_ip, port)
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: is_responsive(url)
    )
    return url


def test_something(http_service):

    response = requests.get(http_service)
    response.raise_for_status()
```

By default this plugin will try to open `docker-compose.yml` in your
`tests` directory. If you need to use a custom location, override the
`docker_compose_file` fixture inside your `conftest.py` file::

```python
import os
import pytest


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "mycustomdir", "docker-compose.yml")
```


# Contributing
This pytest plug-in and its source code are made available to you under a MIT
license. It is safe to use in commercial and closed-source applications. Read
the license for details!

Found a bug? Think a new feature would make this plug-in more practical? We
welcome issues and pull requests!
