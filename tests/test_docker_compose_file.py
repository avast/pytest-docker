# -*- coding: utf-8 -*-


from pytest_docker import docker_compose_file


def test_docker_compose_file():
    docker_compose_file() == 'docker-compose.yml'
