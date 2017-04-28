# -*- coding: utf-8 -*-

import os


def test_docker_compose_project(docker_compose_project_name):
    assert docker_compose_project_name == "pytest{}".format(os.getpid())
