#################################################
  pytest-docker: Docker-based integration tests
#################################################

Description
===========

Simple `py.test`_ fixtures for writing integration tests based on Docker
containers.  Specify all containers you need and ``pytest-docker`` will use
`Docker Compose`_ to spin them up for the duration of your test suite.

.. _`py.test`: http://doc.pytest.org/
.. _`Docker Compose`: https://docs.docker.com/compose/

Usage
=====

Here is the basic recipe for writing a test that depends on a service that
responds over HTTP::

   import pytest
   import requests

   from requests.exceptions import (
       ConnectionError,
   )

   def is_responsive(url):
       """Check if something responds to ``url``."""
       try:
           response = requests.get(url)
           if response.status_code == 200:
               return True
       except ConnectionError:
           return False

   @pytest.fixture(scope='session')
   def some_http_service(docker_ip, docker_services):
       """Ensure that "some service" is up and responsive."""
       url = 'http://' % (
           docker_ip,
           docker_services.port_for('abc', 123),
       )
       docker_services.wait_until_responsive(
          timeout=30.0, pause=0.1,
          check=lambda: is_responsive(url)
       )
       return url

   def test_something(some_service):
       """Sample test."""
       response = requests.get(some_service)
       response.raise_for_status()
 

Contributing
============

This py.test plug-in and its source code are made available to your under and
MIT license.  It is safe to use in commercial and closed-source applications.
Read the license for details!

Found a bug?  Think a new feature would make this plug-in more practical?  No
one is paid to support this software, but we welcome pull requests!
