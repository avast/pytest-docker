# Changelog

## Version 0.13.0
Feat:
- In get_docker_ip(), if `DOCKER_HOST` is using the `unix:` scheme then return "127.0.0.1"

## Version 0.12.0
Changes:
- Add `docker_setup` fixture to allow custom setup actions for docker-compose
(contributed by @raddessi)

## Version 0.11.0
Changes:
- Add support for `pytest` v7 (contributed by @skshetry)

## Version 0.10.3
Changes:
- Ensure that Docker cleanup is executed even with after tests have failed

## Version 0.10.2
Changes:
- Allow higher version of `attrs` (21.0)

## Version 0.10.1
Changes:
- Allow higher version of `attrs`

## Version 0.10.0
Changes:
- Drop Python3.5 support

## Version 0.9.0
Changes:
- Add the `docker_cleanup` fixture to allow custom cleanup actions for
docker-compose

## Version 0.8.0
Changes:
- Add explicit dependencies on `docker-compose` and `pytest`
- Stop using deprecated `pytest-runner` to run package tests

## Version 0.7.2
Changes:
- Update package README

## Version 0.7.1
- Minor packaging related fixes
	- Fix description content type in `setup.cfg`
	- Add `skip_cleanup` option to travis-ci settings

## Version 0.7.0
- Removed the fallback method that allowed running without Docker
- Package cleanup

## Version 0.6.0
- Added ability to return list of files from `docker_compose_file` fixture

## Version 0.3.0
- Added `--build` option to `docker-compose up` command to automatically
  rebuild local containers
