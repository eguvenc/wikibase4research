
## ✅ Example: Simplest Wikibase Installation

```bash
git clone https://gitlab.com/nfdi4culture/wikibase4research/wikibase4research.git
cd wikibase4research
mkdir -p wikiProjects/myWikibase
cp -r wikiPresets/wikibase_plain/* wikiProjects/myWikibase
cp wikiProjects/myWikibase/config/.env.template wikiProjects/myWikibase/config/.env
./wiki.sh wikiProjects/myWikibase setup
```

Open in browser: [http://wb.local](http://wb.local)