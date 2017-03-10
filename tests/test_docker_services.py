# -*- coding: utf-8 -*-


import mock
import pytest
import subprocess

from pytest_docker import (
    docker_services,
    Services,
)


def test_docker_services():
    """Automatic teardown of all services."""

    with mock.patch('subprocess.check_output') as check_output:
        check_output.side_effect = [b'', b'0.0.0.0:32770', b'']
        check_output.returncode = 0

        assert check_output.call_count == 0

        # The fixture is a context-manager.
        gen = docker_services('docker-compose.yml', allow_no_docker=False)
        services = next(gen)
        assert isinstance(services, Services)

        assert check_output.call_count == 1

        # Can request port for services.
        port = services.port_for('abc', 123)
        assert port == 32770

        assert check_output.call_count == 2

        # 2nd request for same service should hit the cache.
        port = services.port_for('abc', 123)
        assert port == 32770

        assert check_output.call_count == 2

        # Next yield is last.
        with pytest.raises(StopIteration):
            print(next(gen))

        assert check_output.call_count == 3

    # Both should have been called.
    assert check_output.call_args_list == [
        mock.call(
            'docker-compose -f "docker-compose.yml" up -d',
            shell=True, stderr=subprocess.STDOUT,
        ),
        mock.call(
            'docker-compose -f "docker-compose.yml" port abc 123',
            shell=True, stderr=subprocess.STDOUT,
        ),
        mock.call(
            'docker-compose -f "docker-compose.yml" down',
            shell=True, stderr=subprocess.STDOUT,
        ),
    ]


def test_docker_services_unused_port():
    """Complain loudly when the requested port is not used by the service."""

    with mock.patch('subprocess.check_output') as check_output:
        check_output.side_effect = [b'', b'', b'']
        check_output.returncode = 0

        assert check_output.call_count == 0

        # The fixture is a context-manager.
        gen = docker_services('docker-compose.yml', allow_no_docker=False)
        services = next(gen)
        assert isinstance(services, Services)

        assert check_output.call_count == 1

        # Can request port for services.
        with pytest.raises(ValueError) as exc:
            print(services.port_for('abc', 123))
        assert str(exc.value) == (
            'Could not detect port for "%s:%d".' % ('abc', 123)
        )

        assert check_output.call_count == 2

        # Next yield is last.
        with pytest.raises(StopIteration):
            print(next(gen))

        assert check_output.call_count == 3

    # Both should have been called.
    assert check_output.call_args_list == [
        mock.call(
            'docker-compose -f "docker-compose.yml" up -d',
            shell=True, stderr=subprocess.STDOUT,
        ),
        mock.call(
            'docker-compose -f "docker-compose.yml" port abc 123',
            shell=True, stderr=subprocess.STDOUT,
        ),
        mock.call(
            'docker-compose -f "docker-compose.yml" down',
            shell=True, stderr=subprocess.STDOUT,
        ),
    ]


def test_docker_services_failure():
    """Propagate failure to start service."""

    with mock.patch('subprocess.check_output') as check_output:
        check_output.side_effect = [
            subprocess.CalledProcessError(
                1, 'the command', b'the output',
            ),
        ]
        check_output.returncode = 1

        # The fixture is a context-manager.
        gen = docker_services('docker-compose.yml', allow_no_docker=False)

        assert check_output.call_count == 0

        # Failure propagates with improved diagnoatics.
        with pytest.raises(Exception) as exc:
            print(next(gen))
        assert str(exc.value) == (
            'Command %r returned %d: """%s""".' % (
                "the command", 1, 'the output',
            )
        )

        assert check_output.call_count == 1

    # Tear down code should not be called.
    assert check_output.call_args_list == [
        mock.call(
            'docker-compose -f "docker-compose.yml" up -d',
            shell=True, stderr=subprocess.STDOUT,
        ),
    ]


def test_wait_until_responsive_timeout():
    clock = mock.MagicMock()
    clock.side_effect = [0.0, 1.0, 2.0, 3.0]

    with mock.patch('time.sleep') as sleep:
        services = Services(compose_file='docker-compose.yml')
        with pytest.raises(Exception) as exc:
            print(services.wait_until_responsive(
                check=lambda: False,
                timeout=3.0,
                pause=1.0,
                clock=clock,
            ))
        assert sleep.call_args_list == [
            mock.call(1.0),
            mock.call(1.0),
            mock.call(1.0),
        ]
    assert str(exc.value) == (
        'Timeout reached while waiting on service!'
    )


def test_get_port_allow_no_docker_docker_online():
    with mock.patch('subprocess.check_output') as check_output:
        check_output.side_effect = [b'', b'', b'0.0.0.0:32770', b'']
        check_output.returncode = 0

        assert check_output.call_count == 0

        # The fixture is a context-manager.
        gen = docker_services('docker-compose.yml', allow_no_docker=True)
        services = next(gen)
        assert isinstance(services, Services)

        assert check_output.call_count == 2

        # Can request port for services.
        port = services.port_for('abc', 123)
        assert port == 32770

        assert check_output.call_count == 3

        # Next yield is last.
        with pytest.raises(StopIteration):
            print(next(gen))

        assert check_output.call_count == 4

    assert check_output.call_args_list == [
        mock.call(
            'docker ps',
            shell=True, stderr=subprocess.STDOUT,
        ),
        mock.call(
            'docker-compose -f "docker-compose.yml" up -d',
            shell=True, stderr=subprocess.STDOUT,
        ),
        mock.call(
            'docker-compose -f "docker-compose.yml" port abc 123',
            shell=True, stderr=subprocess.STDOUT,
        ),
        mock.call(
            'docker-compose -f "docker-compose.yml" down',
            shell=True, stderr=subprocess.STDOUT,
        ),
    ]


def test_get_port_allow_no_docker_docker_offline():
    with mock.patch('subprocess.check_output') as check_output:
        check_output.side_effect = [
            subprocess.CalledProcessError(
                1, 'the command', b'the output',
            ),
        ]
        check_output.returncode = 1

        gen = docker_services('docker-compose.yml', allow_no_docker=True)
        services = next(gen)
        assert services.port_for('abc', 123) == 123

        # Next yield is last.
        with pytest.raises(StopIteration):
            print(next(gen))
