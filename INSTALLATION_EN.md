
# Wikibase4Research – English Installation Guide

Wikibase4Research allows you to easily set up **MediaWiki**, **SemanticMediaWiki (SMW)**, **Wikibase**, or **SemanticWikibase** systems with selected extensions using Docker Compose.
All operations are managed via the `wiki.sh` script.

---

## 🚀 Prerequisites

* **Docker** and **Docker Compose v2**
* **Git**

For Ubuntu/Debian:

```bash
# 1) Remove old versions if any
sudo apt remove docker docker-engine docker.io containerd runc

# 2) Install required packages
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

# 3) Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 4) Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5) Install Docker and plugins
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6) Test installation
docker compose version
sudo usermod -aG docker $USER
newgrp docker
```

## How to Create Your Own Wikibase4Research Project

This guide explains how to set up a custom Wikibase4Research project using a preset as a starting point.

## 1️⃣ Create Your Project Folder

First, clone the main Wikibase4Research repository:

```bash
git clone https://gitlab.com/nfdi4culture/wikibase4research/wikibase4research.git wbLocal
cd wbLocal
```

Create a folder for your custom project. Recommended structure: wikiProjects folder:

```bash
mkdir -p wikiProjects/wbLocal
```

> Replace `wbLocal` with your preferred project name.


## 2️⃣ Initialize a Git Repository

Inside your project folder, initialize a git repository to track your changes:

```bash
git init wikiProjects/wbLocal
```

## 3️⃣ Copy a Matching Preset

Choose a preset that matches your needs and copy it to your project folder. For example, an empty Wikibase:

```bash
cp -r wikiPresets/wikibase_plain/* wikiProjects/wbLocal
```

> You can use other presets as well (`semanticMediawiki_plain`, `wikibase_nfdi4culture`, etc.).

## 📌 Preset Options

* `mediawiki_plain` → Only MediaWiki
* `semanticMediawiki_plain` → SMW-focused
* `wikibase_plain` → Empty Wikibase + services
* `wikibase_nfdi4culture` → Includes data model initialization script
* `semanticWikibase_plain` → Wikibase + SMW together

## 4️⃣ Customize Your Project

Add your own settings and content:

1. Copy the environment template:

```bash
cp wikiProjects/wbLocal/config/.env.template wikiProjects/wbLocal/config/.env
```

2. Edit `.env` and set `W4R_INIT_FOLDER` to your project folder:

```env
W4R_INIT_FOLDER=wikiProjects/wbLocal
```

**Important settings:**

* `W4R_MW_VERSION="1.39"` – MediaWiki version
* `W4R_MW_WIKI_NAME="MyWiki"` – Site name
* `W4R_MW_ADMIN_USER="Admin"` / `W4R_MW_ADMIN_PASS="changeme123"` – Admin account
* `W4R_SERVER_NAME="wb.local"` – Host name
* `W4R_INIT_FOLDER="./wikiProjects/wbLocal"` – Points to the project folder
* `W4R_COMPOSER_SERVICE_INCLUDE=control,elasticsearch,openrefine,wbjobrunner,wdqs,wiki` – Services to run
* `W4R_REVERSEPROXY_PORT=80` – Proxy port


3. Customize other settings:

   * Wiki name: `W4R_MW_WIKI_NAME`
   * Admin user, password, email: `W4R_MW_ADMIN_USER`, `W4R_MW_ADMIN_PASS`, `W4R_MW_ADMIN_EMAIL`
   * URLs: `W4R_SERVER_NAME`, `W4R_FULL_SERVER_NAME`

4. Optional: manage extensions via `config/extensionManagement.json` and `config/composer.local.json`.

5. Optional: add extra content:

   * `fonts/` → custom fonts
   * `images/import/` → images to import via MediaWiki
   * `images/copy/` → images available via web
   * `pages/` → page dumps (XML)
   * `scripts/` → custom Python or Bash scripts


## 5️⃣ First Git Commit

Save your changes:

```bash
cd wikiProjects/wbLocal
git add .
git commit -m "Initial commit"
```

## 6️⃣ Push to a Remote Repository

Create a repo on GitHub or GitLab and push your project:

```bash
git remote add origin git@github.com:USERNAME/REPO_NAME.git
git push -u origin master
```

## 7️⃣ Start the Wiki

Go back to the main Wikibase4Research folder and run the setup command:

```bash
cd ../
./wiki.sh wikiProjects/myProject setup
```

Open your browser at: `http://wb.local`

> Make sure you added `127.0.0.1 wb.local` to your hosts file.

---

## 8️⃣ Import Content and Data

* XML dump import: `./wiki.sh wikiProjects/myProject importdump`
* SQL dump import (faster, overwrites accounts): `./wiki.sh wikiProjects/myProject importmysqldump`
* Customize WDQS and OpenRefine via `prefixes.conf` and `openrefine-manifest.json`.

---

💡 **Summary:**

1. Clone main repo → create your project folder → copy a preset
2. Edit `.env` and extension settings → add content
3. Git commit & push → run setup to start your wiki


## Testing Job Runner:

```
./wiki.sh wikiProjects/wbLocal command "php maintenance/runJobs.php"

Fatal error: Uncaught ExtensionDependencyError: Tweeki is not compatible with the current MediaWiki core (version 1.39.13), it requires: >= 1.43.0.
 in /var/www/html/includes/registration/ExtensionRegistry.php:432
Stack trace:
#0 /var/www/html/includes/registration/ExtensionRegistry.php(276): ExtensionRegistry->readFromQueue(Array)
#1 /var/www/html/includes/Setup.php(278): ExtensionRegistry->loadFromQueue()
#2 /var/www/html/maintenance/doMaintenance.php(83): require_once('/var/www/html/i...')
#3 /var/www/html/maintenance/runJobs.php(136): require_once('/var/www/html/m...')
#4 {main}
  thrown in /var/www/html/includes/registration/ExtensionRegistry.php on line 432
```

## How to Restart all Services:

```
./wiki.sh wikiProjects/wbLocal up
```

---

## 🖥 Hosts File

Add to `/etc/hosts`:

```
127.0.0.1 wb.local
127.0.0.1 openrefine.local
127.0.0.1 wdqs-frontend.local
```

If you changed the host name in `.env`, update it here too.

---

## CHANGE SKIN VERSION FROM wbLocal/extensionManagement.json

```json
"skins": {
    "git": {
        "Tweeki": {
            "path": "https://github.com/thaider/Tweeki",
            "version": "REL1_39",
            "custom_folder": "",
            "active": true
        }
    },
    "composer": {

    }
}
```

---

## ▶️ Run the Installation

```bash
./wiki.sh wikiProjects/wbLocal setup
```

Alternative:

```bash
./wiki.sh wikiProjects/wbLocal up --build -d
```

---

## 🌐 Accessing Services

* Wiki → [http://wb.local](http://wb.local)
* Reverse Proxy (Traefik) → [http://localhost:8091/](http://localhost:8091/)
* OpenRefine → [http://openrefine.local](http://openrefine.local)
* WDQS Frontend → [http://wdqs-frontend.local](http://wdqs-frontend.local)

---

## 🔑 First Login

Use the admin user defined in `.env`:
Default: **admin / 12345678**

---

## 🧩 Extensions & Skins

* Extension definitions: `config/extensionManagement.json`
* Two installation methods:

  * **composer** → Installed via Composer
  * **git** → Cloned from the repository

For extra configurations, use the `config/LocalSettings.d/` folder.

---

## 📦 OpenRefine & WDQS

* **OpenRefine**: Update host names in `config/openrefine/` files.
* **WDQS**: Update prefix URLs in `config/wdqs/prefixes.conf`.
* Reload data:

```bash
./wiki.sh wikiProjects/wbLocal munge
```

Add TTL file:

```bash
./wiki.sh wikiProjects/wbLocal addttl path/to/file.ttl
```

---

## 💾 Backup & Restore

**XML Dump:**

```bash
./wiki.sh wikiProjects/wbLocal exportdump
./wiki.sh wikiProjects/wbLocal importdump
```

**MySQL Dump:**

```bash
./wiki.sh wikiProjects/wbLocal mysqldump
./wiki.sh wikiProjects/wbLocal importmysqldump export/YYYY-MM-DD.sql
```

**Full package:**

```bash
./wiki.sh wikiProjects/wbLocal export
./wiki.sh wikiProjects/wbLocal export-small
```

> Note: Images are stored in `wb_resources/images/` and should also be copied.

---

## 🔄 Update & Remove

* Update:

```bash
./wiki.sh wikiProjects/wbLocal update
```

* Remove (all data will be deleted):

```bash
./wiki.sh wikiProjects/wbLocal remove
```

---

## 🔧 Useful Commands

* Run command inside container:

```bash
./wiki.sh wikiProjects/wbLocal command "php maintenance/runJobs.php"
```

* Fix file permissions:

```bash
./wiki.sh wikiProjects/wbLocal fixpermissions
```
---

Open in browser: [http://wb.local](http://wb.local)

---

## 🔗 Resources

* Original project: [Wikibase4Research](https://gitlab.com/nfdi4culture/wikibase4research/wikibase4research)