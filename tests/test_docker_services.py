import subprocess
from unittest import mock

import pytest
from pytest_docker.plugin import (
    DockerComposeExecutor,
    Services,
    get_cleanup_command,
    get_docker_services,
    get_setup_command,
)


def test_docker_services() -> None:
    """Automatic teardown of all services."""

    with mock.patch("subprocess.check_output") as check_output:
        check_output.side_effect = [b"", b"0.0.0.0:32770", b""]
        check_output.returncode = 0

        assert check_output.call_count == 0

        # The fixture is a context-manager.
        with get_docker_services(
            "docker compose",
            "docker-compose.yml",
            docker_compose_project_name="pytest123",
            docker_setup=get_setup_command(),
            docker_cleanup=get_cleanup_command(),
        ) as services:
            assert isinstance(services, Services)

            assert check_output.call_count == 1

            # Can request port for services.
            port = services.port_for("abc", 123)
            assert port == 32770

            assert check_output.call_count == 2

            # 2nd request for same service should hit the cache.
            port = services.port_for("abc", 123)
            assert port == 32770

            assert check_output.call_count == 2

        assert check_output.call_count == 3

    # Both should have been called.
    assert check_output.call_args_list == [
        mock.call(
            'docker compose -f "docker-compose.yml" -p "pytest123" up --build -d',
            stderr=subprocess.STDOUT,
            shell=True,
        ),
        mock.call(
            'docker compose -f "docker-compose.yml" -p "pytest123" port abc 123',
            stderr=subprocess.STDOUT,
            shell=True,
        ),
        mock.call(
            'docker compose -f "docker-compose.yml" -p "pytest123" down -v',
            stderr=subprocess.STDOUT,
            shell=True,
        ),
    ]


def test_docker_services_unused_port() -> None:
    """Complain loudly when the requested port is not used by the service."""

    with mock.patch("subprocess.check_output") as check_output:
        check_output.side_effect = [b"", b"", b""]
        check_output.returncode = 0

        assert check_output.call_count == 0

        # The fixture is a context-manager.
        with get_docker_services(
            "docker compose",
            "docker-compose.yml",
            docker_compose_project_name="pytest123",
            docker_setup=get_setup_command(),
            docker_cleanup=get_cleanup_command(),
        ) as services:
            assert isinstance(services, Services)

            assert check_output.call_count == 1

            # Can request port for services.
            with pytest.raises(ValueError) as exc:
                print(services.port_for("abc", 123))
            assert str(exc.value) == ('Could not detect port for "%s:%d".' % ("abc", 123))

            assert check_output.call_count == 2

        assert check_output.call_count == 3

    # Both should have been called.
    assert check_output.call_args_list == [
        mock.call(
            'docker compose -f "docker-compose.yml" -p "pytest123" '
            "up --build -d",  # pylint: disable:=implicit-str-concat
            shell=True,
            stderr=subprocess.STDOUT,
        ),
        mock.call(
            'docker compose -f "docker-compose.yml" -p "pytest123" '
            "port abc 123",  # pylint: disable:=implicit-str-concat
            shell=True,
            stderr=subprocess.STDOUT,
        ),
        mock.call(
            'docker compose -f "docker-compose.yml" -p "pytest123" down -v',  # pylint: disable:=implicit-str-concat
            shell=True,
            stderr=subprocess.STDOUT,
        ),
    ]


def test_docker_services_failure() -> None:
    """Propagate failure to start service."""

    with mock.patch("subprocess.check_output") as check_output:
        check_output.side_effect = [subprocess.CalledProcessError(1, "the command", b"the output")]
        check_output.returncode = 1

        # The fixture is a context-manager.
        with pytest.raises(Exception) as exc:
            with get_docker_services(
                "docker compose",
                "docker-compose.yml",
                docker_compose_project_name="pytest123",
                docker_setup=get_setup_command(),
                docker_cleanup=get_cleanup_command(),
            ):
                pass

        # Failure propagates with improved diagnoatics.
        assert str(exc.value) == (
            'Command {} returned {}: """{}""".'.format("the command", 1, "the output")
        )

        assert check_output.call_count == 1

    # Tear down code should not be called.
    assert check_output.call_args_list == [
        mock.call(
            'docker compose -f "docker-compose.yml" -p "pytest123" '
            "up --build -d",  # pylint: disable:=implicit-str-concat
            shell=True,
            stderr=subprocess.STDOUT,
        )
    ]


def test_wait_until_responsive_timeout() -> None:
    clock = mock.MagicMock()
    clock.side_effect = [0.0, 1.0, 2.0, 3.0]

    with mock.patch("time.sleep") as sleep:
        docker_compose = DockerComposeExecutor(
            compose_command="docker compose",
            compose_files="docker-compose.yml",
            compose_project_name="pytest123",
        )
        services = Services(docker_compose)
        with pytest.raises(Exception) as exc:
            print(
                services.wait_until_responsive(  # type: ignore
                    check=lambda: False, timeout=3.0, pause=1.0, clock=clock
                )
            )
        assert sleep.call_args_list == [mock.call(1.0), mock.call(1.0), mock.call(1.0)]
    assert str(exc.value) == ("Timeout reached while waiting on service!")


def test_single_commands() -> None:
    """Ensures backwards compatibility with single command strings for setup and cleanup."""

    with mock.patch("subprocess.check_output") as check_output:
        check_output.returncode = 0

        assert check_output.call_count == 0

        # The fixture is a context-manager.
        with get_docker_services(
            "docker compose",
            "docker-compose.yml",
            docker_compose_project_name="pytest123",
            docker_setup="up --build -d",
            docker_cleanup="down -v",
        ) as services:
            assert isinstance(services, Services)

            assert check_output.call_count == 1

            # Can request port for services.
            port = services.port_for("hello", 80)
            assert port == 1

            assert check_output.call_count == 2

            # 2nd request for same service should hit the cache.
            port = services.port_for("hello", 80)
            assert port == 1

            assert check_output.call_count == 2

        assert check_output.call_count == 3

    # Both should have been called.
    assert check_output.call_args_list == [
        mock.call(
            'docker compose -f "docker-compose.yml" -p "pytest123" up --build -d',
            stderr=subprocess.STDOUT,
            shell=True,
        ),
        mock.call(
            'docker compose -f "docker-compose.yml" -p "pytest123" port hello 80',
            stderr=subprocess.STDOUT,
            shell=True,
        ),
        mock.call(
            'docker compose -f "docker-compose.yml" -p "pytest123" down -v',
            stderr=subprocess.STDOUT,
            shell=True,
        ),
    ]


def test_multiple_commands() -> None:
    """Multiple startup and cleanup commands should be executed."""

    with mock.patch("subprocess.check_output") as check_output:
        check_output.returncode = 0

        assert check_output.call_count == 0

        # The fixture is a context-manager.
        with get_docker_services(
            "docker compose",
            "docker-compose.yml",
            docker_compose_project_name="pytest123",
            docker_setup=["ps", "up --build -d"],
            docker_cleanup=["down -v", "ps"],
        ) as services:
            assert isinstance(services, Services)

            assert check_output.call_count == 2

            # Can request port for services.
            port = services.port_for("hello", 80)
            assert port == 1

            assert check_output.call_count == 3

            # 2nd request for same service should hit the cache.
            port = services.port_for("hello", 80)
            assert port == 1

            assert check_output.call_count == 3

        assert check_output.call_count == 5

    # Both should have been called.
    assert check_output.call_args_list == [
        mock.call(
            'docker compose -f "docker-compose.yml" -p "pytest123" ps',
            stderr=subprocess.STDOUT,
            shell=True,
        ),
        mock.call(
            'docker compose -f "docker-compose.yml" -p "pytest123" up --build -d',
            stderr=subprocess.STDOUT,
            shell=True,
        ),
        mock.call(
            'docker compose -f "docker-compose.yml" -p "pytest123" port hello 80',
            stderr=subprocess.STDOUT,
            shell=True,
        ),
        mock.call(
            'docker compose -f "docker-compose.yml" -p "pytest123" down -v',
            stderr=subprocess.STDOUT,
            shell=True,
        ),
        mock.call(
            'docker compose -f "docker-compose.yml" -p "pytest123" ps',
            stderr=subprocess.STDOUT,
            shell=True,
        ),
    ]
