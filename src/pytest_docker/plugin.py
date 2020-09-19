import contextlib
import os
import re
import subprocess
import time
import timeit

import attr

import pytest


def execute(command, success_codes=(0,)):
    """Run a shell command."""
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        status = 0
    except subprocess.CalledProcessError as error:
        output = error.output or b""
        status = error.returncode
        command = error.cmd

    if status not in success_codes:
        raise Exception(
            'Command {} returned {}: """{}""".'.format(
                command, status, output.decode("utf-8")
            )
        )
    return output


def get_docker_ip():
    # When talking to the Docker daemon via a UNIX socket, route all TCP
    # traffic to docker containers via the TCP loopback interface.
    docker_host = os.environ.get("DOCKER_HOST", "").strip()
    if not docker_host:
        return "127.0.0.1"

    match = re.match(r"^tcp://(.+?):\d+$", docker_host)
    if not match:
        raise ValueError('Invalid value for DOCKER_HOST: "%s".' % (docker_host,))
    return match.group(1)


@pytest.fixture(scope="session")
def docker_ip():
    """Determine the IP address for TCP connections to Docker containers."""

    return get_docker_ip()


@attr.s(frozen=True)
class Services:

    _docker_compose = attr.ib()
    _services = attr.ib(init=False, default=attr.Factory(dict))

    def port_for(self, service, container_port):
        """Return the "host" port for `service` and `container_port`.

        E.g. If the service is defined like this:

            version: '2'
            services:
              httpbin:
                build: .
                ports:
                  - "8000:80"

        this method will return 8000 for container_port=80.
        """

        # Lookup in the cache.
        cache = self._services.get(service, {}).get(container_port, None)
        if cache is not None:
            return cache

        output = self._docker_compose.execute("port %s %d" % (service, container_port))
        endpoint = output.strip().decode("utf-8")
        if not endpoint:
            raise ValueError(
                'Could not detect port for "%s:%d".' % (service, container_port)
            )

        # This handles messy output that might contain warnings or other text
        if len(endpoint.split("\n")) > 1:
            endpoint = endpoint.split("\n")[-1]

        # Usually, the IP address here is 0.0.0.0, so we don't use it.
        match = int(endpoint.split(":", 1)[1])

        # Store it in cache in case we request it multiple times.
        self._services.setdefault(service, {})[container_port] = match

        return match

    def wait_until_responsive(self, check, timeout, pause, clock=timeit.default_timer):
        """Wait until a service is responsive."""

        ref = clock()
        now = ref
        while (now - ref) < timeout:
            if check():
                return
            time.sleep(pause)
            now = clock()

        raise Exception("Timeout reached while waiting on service!")


def str_to_list(arg):
    if isinstance(arg, (list, tuple)):
        return arg
    return [arg]


@attr.s(frozen=True)
class DockerComposeExecutor:

    _compose_files = attr.ib(converter=str_to_list)
    _compose_project_name = attr.ib()

    def execute(self, subcommand):
        command = "docker-compose"
        for compose_file in self._compose_files:
            command += ' -f "{}"'.format(compose_file)
        command += ' -p "{}" {}'.format(self._compose_project_name, subcommand)
        return execute(command)


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    """Get an absolute path to the  `docker-compose.yml` file. Override this
    fixture in your tests if you need a custom location."""

    return os.path.join(str(pytestconfig.rootdir), "tests", "docker-compose.yml")


@pytest.fixture(scope="session")
def docker_compose_project_name():
    """Generate a project name using the current process PID. Override this
    fixture in your tests if you need a particular project name."""

    return "pytest{}".format(os.getpid())


def get_cleanup_command():

    return "down -v"


@pytest.fixture(scope="session")
def docker_cleanup():
    """Get the docker_compose command to be executed for test clean-up actions.
     Override this fixture in your tests if you need to change clean-up actions."""

    return get_cleanup_command()


@contextlib.contextmanager
def get_docker_services(
    docker_compose_file, docker_compose_project_name, docker_cleanup
):
    docker_compose = DockerComposeExecutor(
        docker_compose_file, docker_compose_project_name
    )

    # Spawn containers.
    docker_compose.execute("up --build -d")

    # Let test(s) run.
    yield Services(docker_compose)

    # Clean up.
    docker_compose.execute(docker_cleanup)


@pytest.fixture(scope="session")
def docker_services(docker_compose_file, docker_compose_project_name, docker_cleanup):
    """Start all services from a docker compose file (`docker-compose up`).
    After test are finished, shutdown all services (`docker-compose down`)."""

    with get_docker_services(
        docker_compose_file, docker_compose_project_name, docker_cleanup
    ) as docker_service:
        yield docker_service
