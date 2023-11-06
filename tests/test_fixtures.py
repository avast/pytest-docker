import os.path

HERE = os.path.dirname(os.path.abspath(__file__))


def test_docker_compose_file(docker_compose_file: str):
    assert docker_compose_file == os.path.join(HERE, "docker-compose.yml")


def test_docker_compose_project(docker_compose_project_name: str):
    assert docker_compose_project_name == "pytest{}".format(os.getpid())


def test_docker_cleanup(docker_cleanup: str):
    assert docker_cleanup == "down -v"


def test_docker_setup(docker_setup: str):
    assert docker_setup == "up --build -d"


def test_docker_compose_comand(docker_compose_command: str):
    assert docker_compose_command == "docker compose"
