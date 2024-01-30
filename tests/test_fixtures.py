import os.path
from typing import List

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.pytester import Pytester

HERE = os.path.dirname(os.path.abspath(__file__))


def test_docker_compose_file(docker_compose_file: str) -> None:
    assert docker_compose_file == os.path.join(HERE, "docker-compose.yml")


def test_docker_compose_project(docker_compose_project_name: str) -> None:
    assert docker_compose_project_name == "pytest{}".format(os.getpid())


def test_docker_cleanup(docker_cleanup: List[str]) -> None:
    assert docker_cleanup == ["down -v"]


def test_docker_setup(docker_setup: List[str]) -> None:
    assert docker_setup == ["up --build -d"]


def test_docker_compose_comand(docker_compose_command: str) -> None:
    assert docker_compose_command == "docker compose"


def test_default_container_scope(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        @pytest.fixture(scope="session")
        def dummy(docker_cleanup):
            return True

        def test_default_container_scope(dummy):
            assert dummy == True
    """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


@pytest.mark.parametrize("scope", ["session", "module", "class"])
def test_general_container_scope(testdir: Pytester, request: FixtureRequest, scope: str) -> None:
    params = [f"--container-scope={scope}"]
    assert request.config.pluginmanager.hasplugin("docker")

    testdir.makepyfile(
        f"""
        import pytest
        @pytest.fixture(scope="{scope}")
        def dummy(docker_cleanup):
            return True

        def test_default_container_scope(dummy):
            assert dummy == True
    """
    )

    result = testdir.runpytest(*params)
    result.assert_outcomes(passed=1)
