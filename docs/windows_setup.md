# Windows setup

Wikibase4Research uses docker compose and needs to execute a (linux) shellscript to work.
This document describes the installation and usage process for Windows users.


## WSL (Windows subsystem for linux)
Windows is using a tool called `WSL` to make linux environments available to windows users. The other option is to setup a custom docker container or another type of virtual machine that rund linux. We are suggesting to using the `WSL` appraoch

### WSL setup

To install wsl, open a windows Powershell and type 

`wsl --install -d Ubuntu`

This will setup wsl on your machine and create a new virtual linux environment using the common linux distribution `Ubuntu`
You will be asked for a username and a password for this environment. These credentials doesnt have to match your windows username
and are used only within the linux environment.

for more detailled infos, see here: https://learn.microsoft.com/en-us/windows/wsl/install

### Install docker compose in WSL
you need to use `docker compose` within your linux environment. so you need to install it within your wsl

```
#Refresh and install packages
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common libssl-dev libffi-dev git wget nano

#Add user group
sudo groupadd docker
sudo usermod -aG docker ${USER}

#Add docker key and repo
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update

#Install docker and docker-compose
sudo apt-get install -y docker-ce containerd.io docker-compose

#Install docker-compose (if the previous command failed to install)
sudo curl -sSL https://github.com/docker/compose/releases/download/v`curl -s https://github.com/docker/compose/tags | grep "compose/releases/tag" | sed -r 's|.*([0-9]+\.[0-9]+\.[0-9]+).*|\1|p' | head -n 1`/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose
```
## WSL integration in VisualStudio Code

VSCode has an extension for WSL integration. This is very helpful, as it allows you to access and control the wsl from withon your code editor.

https://code.visualstudio.com/docs/remote/wsl

- start VisualStudio
- hit `F1`
- type `wsl`
- select `WSL: connect to wsl uding distro...`
- select Ubuntu wsl  from the list to connect to this environment
- open a terminal to work on the shell within that linux environment
- use wikibase4research like described in the README file: https://gitlab.com/nfdi4culture/wikibase4research/wikibase4research/-/blob/master/README.md
