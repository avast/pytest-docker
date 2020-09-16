import os.path


HERE = os.path.dirname(os.path.abspath(__file__))


def test_docker_compose_file(docker_compose_file):
    assert docker_compose_file == os.path.join(HERE, "docker-compose.yml")


def test_docker_compose_project(docker_compose_project_name):
    assert docker_compose_project_name == "pytest{}".format(os.getpid())


def test_docker_cleanup(docker_cleanup):
    assert docker_cleanup == "down -v"
