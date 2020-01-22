import shutil
import subprocess
from os import path

import requests
from requests.exceptions import ConnectionError


def is_responsive(url):
    """Check if something responds to ``url``."""
    try:
        response = requests.get(url)
        if response.status_code == 204:
            return True
    except ConnectionError:
        return False


def test_main_fixtures_work(docker_ip, docker_services):
    """Showcase the power of our Docker fixtures!"""

    # Build URL to service listening on random port.
    url = "http://%s:%d/" % (docker_ip, docker_services.port_for("hello", 80))

    docker_services.wait_until_responsive(
        check=lambda: is_responsive(url), timeout=30.0, pause=0.1
    )

    # Contact the service.
    response = requests.get(url)
    # this is set up in the test image
    assert response.status_code == 204


def test_containers_and_volumes_get_cleaned_up(testdir, tmpdir, docker_compose_file):
    _copy_compose_files_to_testdir(testdir, docker_compose_file)

    project_name_file_path = path.join(str(tmpdir), "project_name.txt")
    testdir.makepyfile(
        """
    import subprocess

    def _check_volume_exists(project_name):
        check_proc = subprocess.Popen(
            "docker volume ls".split(),
            stdout=subprocess.PIPE,
        )
        assert project_name.encode() in check_proc.stdout.read()

    def _check_container_exists(project_name):
        check_proc = subprocess.Popen(
            "docker ps".split(),
            stdout=subprocess.PIPE,
        )
        assert project_name.encode() in check_proc.stdout.read()

    def test_whatever(docker_services, docker_compose_project_name):
        _check_volume_exists(docker_compose_project_name)
        _check_container_exists(docker_compose_project_name)
        with open('{}', 'w') as project_name_file:
            project_name_file.write(docker_compose_project_name)
    """.format(
            str(project_name_file_path)
        )
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)

    with open(str(project_name_file_path), "rb") as project_name_file:
        compose_project_name = project_name_file.read().decode()
    _check_volume_is_gone(compose_project_name)
    _check_container_is_gone(compose_project_name)


def _copy_compose_files_to_testdir(testdir, compose_file_path):
    directory_for_compose_files = testdir.mkdir("tests")
    shutil.copy(compose_file_path, str(directory_for_compose_files))

    container_build_files_dir = path.realpath(
        path.join(compose_file_path, "../containers")
    )
    shutil.copytree(
        container_build_files_dir, str(directory_for_compose_files) + "/containers"
    )


def _check_volume_is_gone(project_name):
    check_proc = subprocess.Popen("docker volume ls".split(), stdout=subprocess.PIPE)
    assert project_name.encode() not in check_proc.stdout.read()


def _check_container_is_gone(project_name):
    check_proc = subprocess.Popen("docker ps".split(), stdout=subprocess.PIPE)
    assert project_name.encode() not in check_proc.stdout.read()
