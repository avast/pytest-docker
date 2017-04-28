# -*- coding: utf-8 -*-
import mock
import subprocess

from pytest_docker import DockerComposeExecutor


def test_execute():
    docker_compose = DockerComposeExecutor("docker-compose.yml", "pytest123")
    with mock.patch('subprocess.check_output') as check_output:
        docker_compose.execute("up")
        assert check_output.call_args_list == [
            mock.call(
                'docker-compose -f "docker-compose.yml" -p "pytest123" up',
                shell=True, stderr=subprocess.STDOUT,
            ),
        ]
