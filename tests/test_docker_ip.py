from typing import Dict
from unittest import mock

import pytest
from pytest_docker.plugin import get_docker_ip


def test_docker_ip_native() -> None:
    environ: Dict[str, str] = {}
    with mock.patch("os.environ", environ):
        assert get_docker_ip() == "127.0.0.1"


def test_docker_ip_remote() -> None:
    environ = {"DOCKER_HOST": "tcp://1.2.3.4:2376"}
    with mock.patch("os.environ", environ):
        assert get_docker_ip() == "1.2.3.4"


def test_docker_ip_unix() -> None:
    environ = {"DOCKER_HOST": "unix:///run/user/1000/podman/podman.sock"}
    with mock.patch("os.environ", environ):
        assert get_docker_ip() == "127.0.0.1"


@pytest.mark.parametrize("docker_host", ["http://1.2.3.4:2376"])
def test_docker_ip_remote_invalid(docker_host: str) -> None:
    environ = {"DOCKER_HOST": docker_host}
    with mock.patch("os.environ", environ):
        with pytest.raises(ValueError) as exc:
            print(get_docker_ip())
        assert str(exc.value) == ('Invalid value for DOCKER_HOST: "%s".' % (docker_host,))
