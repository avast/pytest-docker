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
        output = error.output or b''
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

    _docker_compose = attr.ib()
    _docker_allow_fallback = attr.ib(default=False)

    _services = attr.ib(init=False, default=attr.Factory(dict))

    def port_for(self, service, port):
        """Get the effective bind port for a service."""

        # Return the container port if we run in no Docker mode.
        if self._docker_allow_fallback:
            return port

        # Lookup in the cache.
        cache = self._services.get(service, {}).get(port, None)
        if cache is not None:
            return cache

        output = self._docker_compose.execute(
            'port %s %d' % (service, port,)
        )
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


def str_to_list(arg):
    if isinstance(arg, (list, tuple)):
        return arg
    return [arg]


@attr.s(frozen=True)
class DockerComposeExecutor(object):
    _compose_files = attr.ib(convert=str_to_list)
    _compose_project_name = attr.ib()

    def execute(self, subcommand):
        command = "docker-compose"
        for compose_file in self._compose_files:
            command += ' -f "{}"'.format(compose_file)
        command += ' -p "{}" {}'.format(self._compose_project_name, subcommand)
        return execute(command)


@pytest.fixture(scope='session')
def docker_compose_file(pytestconfig):
    """Get the docker-compose.yml absolute path.

    Override this fixture in your tests if you need a custom location.

    """
    return os.path.join(
        str(pytestconfig.rootdir),
        'tests',
        'docker-compose.yml'
    )


@pytest.fixture(scope='session')
def docker_compose_project_name():
    """ Generate a project name using the current process' PID.

    Override this fixture in your tests if you need a particular project name.
    """
    return "pytest{}".format(os.getpid())


@pytest.fixture(scope='session')
def docker_allow_fallback():
    """Return if want to run against localhost when docker is not available.

    Override this fixture to return `True` if you want the ability to
    run without docker.

    """
    return False


@pytest.fixture(scope='session')
def docker_services(
    docker_compose_file, docker_allow_fallback, docker_compose_project_name
):
    """Ensure all Docker-based services are up and running."""

    docker_compose = DockerComposeExecutor(
        docker_compose_file, docker_compose_project_name
    )

    # If we allowed to run without Docker, check it's presence
    if docker_allow_fallback is True:
        try:
            execute('docker ps')
        except Exception:
            # Run against localhost
            yield Services(docker_compose, docker_allow_fallback=True)
            return

    # Spawn containers.
    docker_compose.execute('up --build -d')

    # Let test(s) run.
    yield Services(docker_compose)

    # Clean up.
    docker_compose.execute('down -v')


__all__ = (
    'docker_compose_file',
    'docker_ip',
    'docker_services',
)
