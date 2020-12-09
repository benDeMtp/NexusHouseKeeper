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
python3 NexusHouseKeeper.py -h
```

### Remove all versions matching a pattern

``
python3 NexusHouseKeeper.py -u NEXUS_USER -p NEXUS_PASSWORD -r REPOSITORY --nexus-url NEXUS_URL --version-match 1.1.*
``

This command remove all versions beginning with 1.1

### dry run
Don't perform deletion but display which element should be deleted
``
python3 NexusHouseKeeper.py -u NEXUS_USER -p NEXUS_PASSWORD -r REPOSITORY --nexus-url NEXUS_URL --version-match 1.1.* --dryrun
``

### display each version for each components

``
python3 NexusHouseKeeper.py -u NEXUS_USER -p NEXUS_PASSWORD -r REPOSITORY --nexus-url NEXUS_URL -s
``