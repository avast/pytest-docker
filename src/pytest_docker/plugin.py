from concurrent.futures import Future, ThreadPoolExecutor
import contextlib
import os
import re
import subprocess
import time
import timeit
from types import TracebackType
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Type, Union

import attr
import pytest
from _pytest.config import Config
from _pytest.fixtures import FixtureRequest


@pytest.fixture
def container_scope_fixture(request: FixtureRequest) -> Any:
    return request.config.getoption("--container-scope")


def containers_scope(fixture_name: str, config: Config) -> Any:  # pylint: disable=unused-argument
    return config.getoption("--container-scope", "session")


def execute_and_get_output(command: str, success_codes: Iterable[int] = (0,)) -> Union[bytes, Any]:
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
            'Command {} returned {}: """{}""".'.format(command, status, output.decode("utf-8"))
        )
    return output


def execute(command: str, success_codes: Iterable[int] = (0,)) -> None:
    try:
        process = subprocess.run(command, stderr=subprocess.STDOUT, shell=True)
        returncode = process.returncode
    except subprocess.CalledProcessError as error:
        returncode = error.returncode
        command = error.cmd

    if returncode not in success_codes:
        raise Exception(
            'Command {} returned {}'.format(command, returncode)
        )


def get_docker_ip() -> Union[str, Any]:
    # When talking to the Docker daemon via a UNIX socket, route all TCP
    # traffic to docker containers via the TCP loopback interface.
    docker_host = os.environ.get("DOCKER_HOST", "").strip()
    if not docker_host or docker_host.startswith("unix://"):
        return "127.0.0.1"

    match = re.match(r"^tcp://(.+?):\d+$", docker_host)
    if not match:
        raise ValueError('Invalid value for DOCKER_HOST: "%s".' % (docker_host,))
    return match.group(1)


@pytest.fixture(scope=containers_scope)
def docker_ip() -> Union[str, Any]:
    """Determine the IP address for TCP connections to Docker containers."""

    return get_docker_ip()


@attr.s(frozen=True)
class Services(contextlib.AbstractContextManager):  # type: ignore
    _docker_compose: "DockerComposeExecutor" = attr.ib()
    _services: Dict[Any, Dict[Any, Any]] = attr.ib(
        init=False, default=attr.Factory(dict)
    )
    _live_logs: Dict[str, Future[Any]] = attr.ib(init=False, default=attr.Factory(dict))
    _thread_pool_executor: ThreadPoolExecutor = attr.ib(
        init=False,
        default=attr.Factory(lambda: ThreadPoolExecutor(thread_name_prefix="docker_")),
    )

    def port_for(self, service: str, container_port: int) -> int:
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
        cache: int = self._services.get(service, {}).get(container_port, None)
        if cache is not None:
            return cache

        output = self._docker_compose.execute_and_get_output("port %s %d" % (service, container_port))
        endpoint = output.strip().decode("utf-8")
        if not endpoint:
            raise ValueError('Could not detect port for "%s:%d".' % (service, container_port))

        # This handles messy output that might contain warnings or other text
        if len(endpoint.split("\n")) > 1:
            endpoint = endpoint.split("\n")[-1]

        # Usually, the IP address here is 0.0.0.0, so we don't use it.
        match = int(endpoint.split(":", 1)[-1])

        # Store it in cache in case we request it multiple times.
        self._services.setdefault(service, {})[container_port] = match

        return match

    def wait_until_responsive(
        self,
        check: Any,
        timeout: float,
        pause: float,
        clock: Any = timeit.default_timer,
    ) -> None:
        """Wait until a service is responsive."""

        ref = clock()
        now = ref
        while (now - ref) < timeout:
            if check():
                return
            time.sleep(pause)
            now = clock()

        raise Exception("Timeout reached while waiting on service!")

    def display_live_logs(self, service: str) -> None:
        if service in self._live_logs:
            return
        self._live_logs[service] = self._thread_pool_executor.submit(
            self._docker_compose.execute, f"logs {service} -f"
        )

    def close(self) -> None:
        for _, fut in self._live_logs.items():
            _ = fut.cancel()
        self._thread_pool_executor.shutdown(wait=True, cancel_futures=True)

    def __exit__(
        self,
        _exc_type: Optional[Type[BaseException]],
        __exc_value: Optional[BaseException],
        __traceback: Optional[TracebackType],
    ) -> None:
        self.close()
        return None


def str_to_list(arg: Union[str, List[Any], Tuple[Any]]) -> Union[List[Any], Tuple[Any]]:
    if isinstance(arg, (list, tuple)):
        return arg
    return [arg]


@attr.s(frozen=True)
class DockerComposeExecutor:
    _compose_command: str = attr.ib()
    _compose_files: Any = attr.ib(converter=str_to_list)
    _compose_project_name: str = attr.ib()

    def execute_and_get_output(self, subcommand: str) -> Union[bytes, Any]:
        return execute_and_get_output(self._format_cmd(subcommand))

    def execute(self, subcommand: str) -> None:
        execute(self._format_cmd(subcommand))

    def _format_cmd(self, subcommand: str) -> str:
        command = self._compose_command
        for compose_file in self._compose_files:
            command += ' -f "{}"'.format(compose_file)
        command += ' -p "{}" {}'.format(self._compose_project_name, subcommand)
        return command


@pytest.fixture(scope=containers_scope)
def docker_compose_command() -> str:
    """Docker Compose command to use, it could be either `docker compose`
    for Docker Compose V2 or `docker-compose` for Docker Compose
    V1."""

    return "docker compose"


@pytest.fixture(scope=containers_scope)
def docker_compose_file(pytestconfig: Any) -> Union[List[str], str]:
    """Get an absolute path to the  `docker-compose.yml` file. Override this
    fixture in your tests if you need a custom location."""

    return os.path.join(str(pytestconfig.rootdir), "tests", "docker-compose.yml")


@pytest.fixture(scope=containers_scope)
def docker_compose_project_name() -> str:
    """Generate a project name using the current process PID. Override this
    fixture in your tests if you need a particular project name."""

    return "pytest{}".format(os.getpid())


def get_cleanup_command() -> Union[List[str], str]:
    return ["down -v"]


@pytest.fixture(scope=containers_scope)
def docker_cleanup() -> Union[List[str], str]:
    """Get the docker_compose command to be executed for test clean-up actions.
    Override this fixture in your tests if you need to change clean-up actions.
    Returning anything that would evaluate to False will skip this command."""

    return get_cleanup_command()


def get_setup_command() -> Union[List[str], str]:
    return ["up --build -d"]


@pytest.fixture(scope=containers_scope)
def docker_setup() -> Union[List[str], str]:
    """Get the docker_compose command to be executed for test setup actions.
    Override this fixture in your tests if you need to change setup actions.
    Returning anything that would evaluate to False will skip this command."""

    return get_setup_command()


@contextlib.contextmanager
def get_docker_services(
    docker_compose_command: str,
    docker_compose_file: Union[List[str], str],
    docker_compose_project_name: str,
    docker_setup: Union[List[str], str],
    docker_cleanup: Union[List[str], str],
) -> Iterator[Services]:
    docker_compose = DockerComposeExecutor(
        docker_compose_command, docker_compose_file, docker_compose_project_name
    )

    # setup containers.
    if docker_setup:
        # Maintain backwards compatibility with the string format.
        if isinstance(docker_setup, str):
            docker_setup = [docker_setup]
        for command in docker_setup:
            docker_compose.execute(command)

    try:
        # Let test(s) run.
        with Services(docker_compose) as services:
            yield services
    finally:
        # Clean up.
        if docker_cleanup:
            # Maintain backwards compatibility with the string format.
            if isinstance(docker_cleanup, str):
                docker_cleanup = [docker_cleanup]
            for command in docker_cleanup:
                docker_compose.execute(command)


@pytest.fixture(scope=containers_scope)
def docker_services(
    docker_compose_command: str,
    docker_compose_file: Union[List[str], str],
    docker_compose_project_name: str,
    docker_setup: str,
    docker_cleanup: str,
) -> Iterator[Services]:
    """Start all services from a docker compose file (`docker-compose up`).
    After test are finished, shutdown all services (`docker-compose down`)."""

    with get_docker_services(
        docker_compose_command,
        docker_compose_file,
        docker_compose_project_name,
        docker_setup,
        docker_cleanup,
    ) as docker_service:
        yield docker_service
