# -*- coding: utf-8 -*-

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
    url = 'http://%s:%d/' % (
        docker_ip,
        docker_services.port_for('hello', 80),
    )

    docker_services.wait_until_responsive(
        check=lambda: is_responsive(url),
        timeout=30.0,
        pause=0.1,
    )

    # Contact the service.
    response = requests.get(url)
    # this is set up in the test image
    assert response.status_code == 204
