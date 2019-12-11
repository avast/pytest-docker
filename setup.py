# -*- coding: utf-8 -*-


from setuptools import (
    find_packages,
    setup,
)


setup(
    name='pytest-docker',
    url='https://github.com/AndreLouisCaron/pytest-docker',
    version='0.6.1',
    license='MIT',
    maintainer='Andre Caron',
    maintainer_email='andre.l.caron@gmail.com',
    classifiers=[
        'Framework :: Pytest',
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Topic :: Utilities',
        'Intended Audience :: Developers',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
    ],
    keywords=[
        'docker',
        'docker-compose',
        'pytest',
    ],
    packages=find_packages(where='src'),
    package_dir={
        '': 'src',
    },
    entry_points={
        'pytest11': [
            'docker = pytest_docker',
        ],
    },
    install_requires=[
        'attrs>=16',
    ],
)
