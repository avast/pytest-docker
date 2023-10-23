import os.path
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))


def test_docker_compose_file(docker_compose_file):
    assert docker_compose_file == os.path.join(HERE, "docker-compose.yml")


def test_docker_compose_project(docker_compose_project_name):
    assert docker_compose_project_name == "pytest{}".format(os.getpid())


def test_docker_cleanup(docker_cleanup):
    assert docker_cleanup == ["down -v"]



def test_docker_setup(docker_setup):
    assert docker_setup == ["up --build -d"]



def test_docker_compose_command(docker_compose_command):
    assert docker_compose_command == "docker compose"


def test_default_container_scope(pytester):
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
def test_general_container_scope(testdir, request, scope):
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
