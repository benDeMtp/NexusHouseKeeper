# Nexus House Keeper

This project helps nexus users to clean their repository deleting old or unused component

## Requirements:
* Python 3

## Installation
``
pip install -r requirements.txt
``

### Print help :
```
python3 -m nexushousekeeper.NexusHouseKeeper -h
```

### Remove all components with versions matching a pattern

``
python3 -m nexushousekeeper.NexusHouseKeeper -u NEXUS_USER -p NEXUS_PASSWORD -r REPOSITORY --nexus-url NEXUS_URL --version-match 1.1.*
``

This command remove all versions beginning with 1.1

### Remove all components with the exact version

``
python3 -m nexushousekeeper.NexusHouseKeeper -u NEXUS_USER -p NEXUS_PASSWORD -r REPOSITORY --nexus-url NEXUS_URL --version-match 1.1-SNAPSHOT
``

This command remove all component with version 1.1-SNAPSHOT

### dry run
Don't perform deletion but display which element should be deleted
``
python3 -m nexushousekeeper.NexusHouseKeeper -u NEXUS_USER -p NEXUS_PASSWORD -r REPOSITORY --nexus-url NEXUS_URL --version-match 1.1.* --dryrun
``

### display each version for each components

``
python3 -m nexushousekeeper.NexusHouseKeeper -u NEXUS_USER -p NEXUS_PASSWORD -r REPOSITORY --nexus-url NEXUS_URL -s
``

## Build Project
``
python3 setup.py sdist bdist_wheel
``

## Deploy to pypi
* testpypi

``
python3 -m twine upload --repository testpypi dist/*
``