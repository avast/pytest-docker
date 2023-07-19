Docker-based integration tests
=====
[![PyPI version](https://img.shields.io/pypi/v/pytest-docker?color=green)](https://pypi.org/project/pytest-docker/)
[![Build Status](https://github.com/avast/pytest-docker/actions/workflows/tests.yaml/badge.svg?branch=master)](https://github.com/avast/pytest-docker/actions/workflows/tests.yaml)
[![Python versions](https://img.shields.io/pypi/pyversions/pytest-docker)](https://pypi.org/project/pytest-docker/)
[![Code style](https://img.shields.io/badge/formatted%20with-black-black)](https://github.com/psf/black)


# Description
Simple [pytest](http://doc.pytest.org/) fixtures that help you write integration
tests with Docker and [Docker Compose](https://docs.docker.com/compose/).
Specify all necessary containers in a `docker-compose.yml` file and and
`pytest-docker` will spin them up for the duration of your tests.

This package is tested with Python versions `3.6`, `3.7`, `3.8` and
`3.9`, and `pytest` version 4, 5 and 6. Python 2 is not supported.

`pytest-docker` was originally created by André Caron.

# Installation
Install `pytest-docker` with `pip` or add it to your test requirements.

By default, it uses the `docker compose` command, so it relies on the Compose plugin for Docker (also called Docker Compose V2).

## Docker Compose V1 compatibility

If you want to use the old `docker-compose` command (deprecated since July 2023, not receiving updates since 2021)
 then you can do it using the [`docker-compose-command`](#docker_compose_command) fixture:

```python
@pytest.fixture(scope="session")
def docker_compose_command() -> str:
    return "docker-compose"
```

If you want to use the pip-distributed version of `docker-compose` command, you can install it using
```
pip install pytest-docker[docker-compose-v1]
```

Another option could be usage of [`compose-switch`](https://github.com/docker/compose-switch).

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

### `docker_compose_command`

Docker Compose command to use to execute Dockers. Default is to use
Docker Compose V2 (command is `docker compose`). If you want to use
Docker Compose V1, change this fixture to return `docker-compose`.

### `docker_setup`

Get the docker_compose command to be executed for test spawn actions.
Override this fixture in your tests if you need to change spawn actions.
Returning anything that would evaluate to False will skip this command.

### `docker_cleanup`

Get the docker_compose command to be executed for test clean-up actions.
Override this fixture in your tests if you need to change clean-up actions.
Returning anything that would evaluate to False will skip this command.


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
