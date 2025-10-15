
## ✅ Example: Simplest Wikibase Installation

https://gitlab.com/nfdi4culture/wikibase4research/wikibase4research

```bash
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

The init command is quite new. I want to add new collections to it, like Semantic Mediawiki, but right now, I'm not there yet
Sorry, i should mark this as WIP
Copying the folder is the way to go now.


```bash
git clone https://gitlab.com/nfdi4culture/wikibase4research/wikibase4research.git wikidemo
cd wikidemo
git checkout 5339bb94f1e4b907642cc2a83eee3219b0c7a01f

cp -r wikiPresets/semanticWikibase_plain/* wikiProjects/wikidemo
cp wikiProjects/wikidemo/config/.env.template wikiProjects/wikidemo/config/.env

#./wiki.sh init
./wiki.sh wikiProjects/WikiDemo/ setup
```