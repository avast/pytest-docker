# -*- coding: utf-8 -*-


import mock
import pytest

from pytest_docker import docker_ip


def test_docker_ip_native():
    environ = {}
    with mock.patch('os.environ', environ):
        assert docker_ip() == '127.0.0.1'


def test_docker_ip_remote():
    environ = {
        'DOCKER_HOST': 'tcp://1.2.3.4:2376',
    }
    with mock.patch('os.environ', environ):
        assert docker_ip() == '1.2.3.4'


@pytest.mark.parametrize('docker_host', [
    'http://1.2.3.4:2376',
])
def test_docker_ip_remote_invalid(docker_host):
    environ = {
        'DOCKER_HOST': docker_host,
    }
    with mock.patch('os.environ', environ):
        with pytest.raises(ValueError) as exc:
            print(docker_ip())
        assert str(exc.value) == (
            'Invalid value for DOCKER_HOST: "%s".' % (docker_host,)
        )
