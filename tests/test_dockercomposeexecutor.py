import subprocess
from unittest import mock

import py
from pytest_docker.plugin import DockerComposeExecutor


def test_execute() -> None:
    docker_compose = DockerComposeExecutor("docker compose", "docker-compose.yml", "pytest123")
    with mock.patch("subprocess.run") as run:
        run.return_value = subprocess.CompletedProcess([], returncode=0)
        docker_compose.execute("up")
        assert run.call_args_list == [
            mock.call(
                'docker compose -f "docker-compose.yml" -p "pytest123" up',
                shell=True,
                stderr=subprocess.STDOUT,
            )
        ]


def test_execute_docker_compose_v2() -> None:
    docker_compose = DockerComposeExecutor("docker compose", "docker-compose.yml", "pytest123")
    with mock.patch("subprocess.run") as run:
        run.return_value = subprocess.CompletedProcess([], returncode=0)
        docker_compose.execute("up")
        assert run.call_args_list == [
            mock.call(
                'docker compose -f "docker-compose.yml" -p "pytest123" up',
                shell=True,
                stderr=subprocess.STDOUT,
            )
        ]


def test_pypath_compose_files() -> None:
    compose_file: py.path.local = py.path.local("/tmp/docker-compose.yml")
    docker_compose = DockerComposeExecutor("docker compose", compose_file, "pytest123")  # type: ignore
    with mock.patch("subprocess.run") as run:
        run.return_value = subprocess.CompletedProcess([], returncode=0)
        docker_compose.execute("up")
        assert run.call_args_list == [
            mock.call(
                'docker compose -f "/tmp/docker-compose.yml"'
                ' -p "pytest123" up',  # pylint: disable:=implicit-str-concat
                shell=True,
                stderr=subprocess.STDOUT,
            )
        ] or run.call_args_list == [
            mock.call(
                'docker compose -f "C:\\tmp\\docker-compose.yml"'
                ' -p "pytest123" up',  # pylint: disable:=implicit-str-concat
                shell=True,
                stderr=subprocess.STDOUT,
            )
        ]


def test_multiple_compose_files() -> None:
    docker_compose = DockerComposeExecutor(
        "docker compose", ["docker-compose.yml", "other-compose.yml"], "pytest123"
    )
    with mock.patch("subprocess.run") as run:
        run.return_value = subprocess.CompletedProcess([], returncode=0)
        docker_compose.execute("up")
        assert run.call_args_list == [
            mock.call(
                'docker compose -f "docker-compose.yml" -f "other-compose.yml"'
                ' -p "pytest123" up',
                shell=True,
                stderr=subprocess.STDOUT,
            )
        ]
