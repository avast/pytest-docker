# -*- coding: utf-8 -*-


import attr
import os
import pytest
import re
import subprocess
import time
import timeit


def execute(command, success_codes=(0,)):
    """Run a shell command."""
    try:
        output = subprocess.check_output(
            command, stderr=subprocess.STDOUT, shell=True,
        )
        status = 0
    except subprocess.CalledProcessError as error:
        output = error.output
        status = error.returncode
        command = error.cmd
    output = output.decode('utf-8')
    if status not in success_codes:
        raise Exception(
            'Command %r returned %d: """%s""".' % (command, status, output)
        )
    return output


@pytest.fixture(scope='session')
def docker_ip():
    """Determine IP address for TCP connections to Docker containers."""

    # When talking to the Docker daemon via a UNIX socket, route all TCP
    # traffic to docker containers via the TCP loopback interface.
    docker_host = os.environ.get('DOCKER_HOST', '').strip()
    if not docker_host:
        return '127.0.0.1'

    match = re.match('^tcp://(.+?):\d+$', docker_host)
    if not match:
        raise ValueError(
            'Invalid value for DOCKER_HOST: "%s".' % (docker_host,)
        )
    return match.group(1)


@attr.s(frozen=True)
class Services(object):
    """."""

    _compose_file = attr.ib()
    _services = attr.ib(init=False, default=attr.Factory(dict))

    def port_for(self, service, port):
        """Get the effective bind port for a service."""

        # Lookup in the cache.
        cache = self._services.get(service, {}).get(port, None)
        if cache is not None:
            return cache

        output = execute('docker-compose -f "%s" port %s %d' % (
            self._compose_file, service, port,
        ))
        endpoint = output.strip()
        if not endpoint:
            raise ValueError(
                'Could not detect port for "%s:%d".' % (service, port)
            )

        # Usually, the IP address here is 0.0.0.0, so we don't use it.
        match = int(endpoint.split(':', 1)[1])

        # Store it in cache in case we request it multiple times.
        self._services.setdefault(service, {})[port] = match

        return match

    def wait_until_responsive(self, check, timeout, pause,
                              clock=timeit.default_timer):
        """Wait until a service is responsive."""

        ref = clock()
        now = ref
        while (now - ref) < timeout:
            if check():
                return
            time.sleep(pause)
            now = clock()

        raise Exception(
            'Timeout reached while waiting on service!'
        )


@pytest.fixture(scope='session')
def docker_compose_file():
    """."""
    return 'docker-compose.yml'


@pytest.fixture(scope='session')
def docker_services(docker_compose_file):
    """Ensure all Docker-based services are up and running."""

    # Spawn containers.
    execute('docker-compose -f "%s" up -d' % (docker_compose_file,))

    # Let test(s) run.
    yield Services(compose_file=docker_compose_file)

    # Clean up.
    execute('docker-compose -f "%s" down' % (docker_compose_file,))


__all__ = (
    'docker_compose_file',
    'docker_ip',
    'docker_services',
)
