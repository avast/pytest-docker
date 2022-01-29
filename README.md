Docker-based integration tests
=====
[![PyPI version](https://img.shields.io/pypi/v/pytest-docker?color=green)](https://pypi.org/project/pytest-docker/)
[![Build Status](https://github.com/avast/pytest-docker/actions/workflows/tests.yaml/badge.svg?branch=master)](https://github.com/avast/pytest-docker/actions/workflows/tests.yaml)
[![Python versions](https://img.shields.io/pypi/pyversions/pytest-docker)](https://pypi.org/project/pytest-docker/)
[![Code style](https://img.shields.io/badge/formatted%20with-black-black)](https://github.com/psf/black)


# Description
Simple [pytest](http://doc.pytest.org/) fixtures that help you write integration
tests with Docker and [docker-compose](https://docs.docker.com/compose/).
Specify all necessary containers in a `docker-compose.yml` file and and
`pytest-docker` will spin them up for the duration of your tests.

This package is tested with Python versions `3.6`, `3.7`, `3.8` and
`3.9`, and `pytest` version 4, 5 and 6. Python 2 is not supported.

`pytest-docker` was originally created by André Caron.

# Installation
Install `pytest-docker` with `pip` or add it to your test requirements. It is
recommended to install `docker-compose` python package directly in your
environment to ensure that it is available during tests. This will prevent
potential dependency conflicts that can occur when the system wide
`docker-compose` is used in tests.

The default behavior is not to install `docker-compose` at all. If you
want to, you install `pytest-docker` with the `docker-compose` extra,
you can use the following command:

```
pip install pytest-docker[docker-compose-v1]
```


# Usage
Here is an example of a test that depends on a HTTP service.

With a `docker-compose.yml` file like this (using the
[httpbin](https://httpbin.org/) service):

```yaml
version: '2'
services:
  httpbin:
    image: "kennethreitz/httpbin"
    ports:
      - "8000:80"
```

You can write a test like this:

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

    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("httpbin", 80)
    url = "http://{}:{}".format(docker_ip, port)
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: is_responsive(url)
    )
    return url


def test_status_code(http_service):
    status = 418
    response = requests.get(http_service + "/status/{}".format(status))

    assert response.status_code == status
```

By default this plugin will try to open `docker-compose.yml` in your
`tests` directory. If you need to use a custom location, override the
`docker_compose_file` fixture inside your `conftest.py` file:

```python
import os
import pytest


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "mycustomdir", "docker-compose.yml")
```

## Available fixtures
All fixtures have `session` scope.

### `docker_ip`

Determine the IP address for TCP connections to Docker containers.

### `docker_compose_file`

Get an absolute path to the  `docker-compose.yml` file. Override this fixture in
your tests if you need a custom location.

### `docker_compose_project_name`

Generate a project name using the current process PID. Override this fixture in
your tests if you need a particular project name.

### `docker_services`

Start all services from the docker compose file (`docker-compose up`).
After test are finished, shutdown all services (`docker-compose down`).

### `docker_cleanup`

Get the docker compose command to execute for test clean-up actions. Override
this fixture in your tests if you need custom clean-up actions.

# Development
Use of a virtual environment is recommended. See the
[venv](https://docs.python.org/3/library/venv.html) package for more
information.

First, install `pytest-docker` and its test dependencies:

	pip install -e ".[tests]"

Run tests with

	pytest -c setup.cfg

to make sure that the correct configuration is used. This is also how tests are
run in CI.

Use [black](https://pypi.org/project/black/) with default settings for
formatting. You can also use `pylint` with `setup.cfg` as the configuration
file.


# Contributing
This pytest plug-in and its source code are made available to you under a MIT
license. It is safe to use in commercial and closed-source applications. Read
the license for details!

Found a bug? Think a new feature would make this plug-in more practical? We
welcome issues and pull requests!

When creating a pull request, be sure to follow this projects conventions (see
above).
