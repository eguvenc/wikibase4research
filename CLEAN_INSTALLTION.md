
## Create the docker group.

```bash
sudo groupadd docker
```

Add your user to the docker group.

```bash
sudo usermod -aG docker $USER
```

You can also run the following command to activate the changes to groups:

```bash
newgrp docker
```

## Permissions

```bash 
chmod 755 -R /home/ersin/wiki-test/wikiProjects/
```

## Setup

```bash
 ./wiki.sh wikiProjects/TestWiki/ setup
```

## Updating Hash

```bash
./wiki.sh wikiProjects/TestWiki/ updatehash
```