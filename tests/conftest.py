# -*- coding: utf-8 -*-


import os.path
import pytest


HERE = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='session')
def docker_compose_file():
    return os.path.join(HERE, 'docker-compose.yml')
