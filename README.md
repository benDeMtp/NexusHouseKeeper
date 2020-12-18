# Nexus House Keeper

This project helps nexus users to clean their repository deleting old or unused component

## Requirements:
* Python 3

## Installation
Nexus House Keeper can be downloaded from pypi

``
pip install nexushousekeeper
``

### Print help :
```
nexushousekeeper -h
```

### Remove all components with versions matching a pattern

``
nexushousekeeper -u NEXUS_USER -p NEXUS_PASSWORD -r REPOSITORY --nexus-url NEXUS_URL --version-match 1.1.*
``

This command remove all versions beginning with 1.1

### Remove all components with the exact version

``
nexushousekeeper -u NEXUS_USER -p NEXUS_PASSWORD -r REPOSITORY --nexus-url NEXUS_URL --version-match 1.1-SNAPSHOT
``

This command remove all components with version 1.1-SNAPSHOT

### dry run
Don't perform deletion but display which element should be deleted
``
nexushousekeeper -u NEXUS_USER -p NEXUS_PASSWORD -r REPOSITORY --nexus-url NEXUS_URL --version-match 1.1.* --dryrun
``

### display each version for each component

``
nexushousekeeper -u NEXUS_USER -p NEXUS_PASSWORD -r REPOSITORY --nexus-url NEXUS_URL -s
``

## Contributing

## Install

``
poetry install
``

## Run tests

``
poetry run pytest
``

## Build Project

``
poetry build
``

## Deploy to pypi
* testpypi

``
poetry publish -r testpypi 
``