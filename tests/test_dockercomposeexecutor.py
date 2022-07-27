import subprocess
from unittest import mock

import py
from pytest_docker.plugin import DockerComposeExecutor


def test_execute():
    docker_compose = DockerComposeExecutor(
        "docker-compose", "docker-compose.yml", "pytest123"
    )
    with mock.patch("subprocess.check_output") as check_output:
        docker_compose.execute("up")
        assert check_output.call_args_list == [
            mock.call(
                'docker-compose -f "docker-compose.yml" -p "pytest123" up',
                shell=True,
                stderr=subprocess.STDOUT,
            )
        ]


def test_execute_docker_compose_v2():
    docker_compose = DockerComposeExecutor(
        "docker compose", "docker-compose.yml", "pytest123"
    )
    with mock.patch("subprocess.check_output") as check_output:
        docker_compose.execute("up")
        assert check_output.call_args_list == [
            mock.call(
                'docker compose -f "docker-compose.yml" -p "pytest123" up',
                shell=True,
                stderr=subprocess.STDOUT,
            )
        ]


def test_pypath_compose_files():
    compose_file = py.path.local("/tmp/docker-compose.yml")
    docker_compose = DockerComposeExecutor("docker-compose", compose_file, "pytest123")
    with mock.patch("subprocess.check_output") as check_output:
        docker_compose.execute("up")
        assert check_output.call_args_list == [
            mock.call(
                'docker-compose -f "/tmp/docker-compose.yml"' ' -p "pytest123" up',
                shell=True,
                stderr=subprocess.STDOUT,
            )
        ]


def test_multiple_compose_files():
    docker_compose = DockerComposeExecutor(
        "docker-compose", ["docker-compose.yml", "other-compose.yml"], "pytest123"
    )
    with mock.patch("subprocess.check_output") as check_output:
        docker_compose.execute("up")
        assert check_output.call_args_list == [
            mock.call(
                'docker-compose -f "docker-compose.yml" -f "other-compose.yml"'
                ' -p "pytest123" up',
                shell=True,
                stderr=subprocess.STDOUT,
            )
        ]
