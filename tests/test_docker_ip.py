# -*- coding: utf-8 -*-


import mock
import pytest

import pytest_docker
from pytest_docker import docker_ip

IP_FIXTURE_NAME = docker_ip.__name__


def test_docker_ip_native(monkeypatch, testdir):
    monkeypatch.setenv('DOCKER_HOST', '')

    testdir.makepyfile("""
    def test_docker_ip(docker_ip):
        assert docker_ip == '127.0.0.1'
    """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_docker_ip_remote(testdir, monkeypatch):
    monkeypatch.setenv('DOCKER_HOST', 'tcp://1.2.3.4:2376')

    testdir.makepyfile("""
    def test_docker_ip(docker_ip):
        assert docker_ip == '1.2.3.4'
    """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_docker_ip_remote_invalid(monkeypatch, testdir):
    monkeypatch.setenv('DOCKER_HOST', 'http://1.2.3.4:2376')

    testdir.makepyfile("""
    def test_docker_ip_invalid(request):
        with pytest.raises(ValueError) as exc:
            request.getfixturevalue(IP_FIXTURE_NAME)
        assert str(exc.value) == (
            'Invalid value for DOCKER_HOST: "%s".' % (docker_host,)
        )
    """)
