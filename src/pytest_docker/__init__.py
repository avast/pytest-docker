import pytest

from .plugin import (
    docker_cleanup,
    docker_compose_command,
    docker_compose_file,
    docker_compose_project_name,
    docker_ip,
    docker_services,
    docker_setup,
)

__all__ = [
    "docker_compose_command",
    "docker_compose_file",
    "docker_compose_project_name",
    "docker_ip",
    "docker_setup",
    "docker_cleanup",
    "docker_services",
]


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("docker")
    group.addoption(
        "--container-scope",
        type=str,
        action="store",
        default="session",
        help="The pytest fixture scope for reusing containers between tests."
        " For available scopes and descriptions, "
        "   see https://docs.pytest.org/en/6.2.x/fixture.html#fixture-scopes",
    )
