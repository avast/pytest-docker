import os
from pathlib import Path
from typing import List

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.pytester import Pytester


@pytest.fixture
def tests_dir(pytester: Pytester) -> Path:
    dir = Path(pytester.path) / "tests"
    dir.mkdir()
    return dir


@pytest.fixture(params=[[]])
def tests_dir_contents(tests_dir: Path, request: FixtureRequest) -> List[Path]:
    filenames: List[str] = getattr(request, "param", [])
    paths = [tests_dir / filename for filename in filenames]
    for path in paths:
        path.touch()

    return paths


@pytest.mark.parametrize(
    ("tests_dir_contents", "expected_compose_file"),
    [
        (
            [
                "compose.yaml",
                "compose.yml",
                "docker-compose.yaml",
                "docker-compose.yml",
            ],
            "compose.yaml",
        ),
        (["compose.yml", "docker-compose.yaml", "docker-compose.yml"], "compose.yml"),
        (["docker-compose.yaml", "docker-compose.yml"], "docker-compose.yaml"),
        (["docker-compose.yml"], "docker-compose.yml"),
        ([], "docker-compose.yml"),
    ],
    indirect=["tests_dir_contents"],
)
@pytest.mark.usefixtures("tests_dir_contents")
def test_docker_compose_file(
    pytester: Pytester, expected_compose_file: str, tests_dir: Path
) -> None:
    pytester.makepyfile(
        f"""
        def test_docker_compose_file(docker_compose_file):
            assert docker_compose_file == "{tests_dir}/{expected_compose_file}"
    """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_docker_compose_project(docker_compose_project_name: str) -> None:
    assert docker_compose_project_name == "pytest{}".format(os.getpid())


def test_docker_cleanup(docker_cleanup: List[str]) -> None:
    assert docker_cleanup == ["down -v"]


def test_docker_setup(docker_setup: List[str]) -> None:
    assert docker_setup == ["up --build --wait"]


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
