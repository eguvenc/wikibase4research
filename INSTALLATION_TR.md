
# Wikibase4Research – Türkçe Kurulum Rehberi

Wikibase4Research, Docker Compose kullanarak **MediaWiki**, **SemanticMediaWiki (SMW)**, **Wikibase** veya **SemanticWikibase** sistemlerini; seçili eklentilerle birlikte kolayca ayağa kaldırmanı sağlar.  
Tüm işlemler `wiki.sh` komut dosyası ile yönetilir.

---

## 🚀 Önkoşullar

- **Docker** ve **Docker Compose v2**  
- **Git**

Ubuntu/Debian için:

```bash
# 1) Eski varsa kaldır
sudo apt remove docker docker-engine docker.io containerd runc

# 2) Gerekli paketleri yükle
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

# 3) Docker’ın resmi GPG anahtarını ekle
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 4) Docker deposunu ekle
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5) Docker ve pluginleri kur
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6) Test it
docker compose version
sudo usermod -aG docker $USER
newgrp docker
````

---

## 📥 Depoyu Klonlamak

```bash
git clone https://gitlab.com/nfdi4culture/wikibase4research/wikibase4research.git
cd wikibase4research
```

Projen için bir klasör oluştur:

```bash
mkdir -p wikiProjects/testProject
cp -r wikiPresets/wikibase_plain/* wikiProjects/testProject
git -C wikiProjects/testProject init
```

CHANGE SKIN VERSION FROM extensionManagement.json file

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

<!-- 
docker exec -it wikiprojects_testproject-wikibase-1 bash
root@62261f3db565:/var/www/html# ls

cd extensions/

git clone -b REL1_39 https://github.com/thaider/Tweeki.git

chown -R www-data:www-data /var/www/html/extensions/Tweeki


Edit composer.yml  and add this line to mount custom extensions and skins.


- $W4R_INIT_FOLDER/wiki/extensions:/var/www/html/extensions


docker compose --env-file wikiProjects/testProject/config/.env up -d --build wikibase -->


---

## ⚙️ .env Dosyası

Örnek dosyayı kopyala:

```bash
cp wikiProjects/testProject/config/.env.template wikiProjects/testProject/config/.env
```

**Önemli ayarlar:**

* `W4R_MW_VERSION="1.39"` – MediaWiki sürümü
* `W4R_MW_WIKI_NAME="MyWiki"` – Site adı
* `W4R_MW_ADMIN_USER="Admin"` / `W4R_MW_ADMIN_PASS="changeme123"` – Yönetici hesabı
* `W4R_SERVER_NAME="wb.local"` – Host adı
* `W4R_INIT_FOLDER="./wikiProjects/testProject"` – Proje klasörünü işaret etmeli
* `W4R_COMPOSER_SERVICE_INCLUDE=control,elasticsearch,openrefine,wbjobrunner,wdqs,wiki` – Çalışacak servisler
* `W4R_REVERSEPROXY_PORT=80` – Proxy portu

---

## 🖥 Hosts Dosyası

`/etc/hosts` içine ekle:

```
127.0.0.1 wb.local
127.0.0.1 openrefine.local
127.0.0.1 wdqs-frontend.local
```

Eğer `.env` dosyasında host adını değiştirdiysen, burada da güncelle.

---

## ▶️ Kurulumu Çalıştır

```bash
./wiki.sh wikiProjects/testProject setup
```

Alternatif:

```bash
./wiki.sh wikiProjects/testProject up --build -d
```

---

## 🌐 Servislere Erişim

* Wiki → [http://wb.local](http://wb.local)
* Reverse Proxy (Traefik) → [http://localhost:8091/](http://localhost:8091/)
* OpenRefine → [http://openrefine.local](http://openrefine.local)
* WDQS Frontend → [http://wdqs-frontend.local](http://wdqs-frontend.local)

---

## 🔑 İlk Giriş

`.env` dosyasında tanımladığın yönetici kullanıcı ile giriş yapabilirsin:
Varsayılan: **admin / Mbry8992@**

---

## 🧩 Eklentiler ve Skinler

* Eklenti tanımları: `config/extensionManagement.json`
* İki yöntem vardır:

  * **composer** → Composer ile yüklenir
  * **git** → Depodan klonlanır

Ekstra ayarlar için `config/LocalSettings.d/` klasörünü kullanabilirsin.

---

## 📦 OpenRefine & WDQS

* **OpenRefine**: `config/openrefine/` içindeki dosyalarda host adını kendi sitene göre güncelle.
* **WDQS**: `config/wdqs/prefixes.conf` içinde prefix URL’lerini güncelle.
* Veriyi yeniden yüklemek için:

```bash
./wiki.sh wikiProjects/testProject munge
```

TTL dosyası eklemek için:

```bash
./wiki.sh wikiProjects/testProject addttl path/to/file.ttl
```

---

## 💾 İçerik Yedekleme ve Geri Yükleme

**XML Dump:**

```bash
./wiki.sh wikiProjects/testProject exportdump
./wiki.sh wikiProjects/testProject importdump
```

**MySQL Dump:**

```bash
./wiki.sh wikiProjects/testProject mysqldump
./wiki.sh wikiProjects/testProject importmysqldump export/YYYY-MM-DD.sql
```

**Tüm paket:**

```bash
./wiki.sh wikiProjects/testProject export
./wiki.sh wikiProjects/testProject export-small
```

> Not: Görseller `wb_resources/images/` klasöründe tutulur, ayrıca kopyalanmalıdır.

---

## 🔄 Güncelleme & Kaldırma

* Güncelle:

```bash
./wiki.sh wikiProjects/testProject update
```

* Kaldır (tüm veriler silinir):

```bash
./wiki.sh wikiProjects/testProject remove
```

---

## 🔧 Faydalı Komutlar

* Container içinde komut çalıştır:

  ```bash
  ./wiki.sh wikiProjects/testProject command "php maintenance/runJobs.php"
  ```

* Dosya izinlerini düzelt:

  ```bash
  ./wiki.sh wikiProjects/testProject fixpermissions
  ```

---

## 📌 Preset Seçenekleri

* `mediawiki_plain` → Sadece MediaWiki
* `semanticMediawiki_plain` → SMW odaklı
* `wikibase_plain` → Boş Wikibase + servisler
* `wikibase_nfdi4culture` → Veri modeli başlatan script ile
* `semanticWikibase_plain` → Wikibase + SMW birlikte

---

## ✅ Örnek: En Basit Wikibase Kurulumu

```bash
git clone https://gitlab.com/nfdi4culture/wikibase4research/wikibase4research.git
cd wikibase4research
mkdir -p wikiProjects/myWikibase
cp -r wikiPresets/wikibase_plain/* wikiProjects/myWikibase
cp wikiProjects/myWikibase/config/.env.template wikiProjects/myWikibase/config/.env
./wiki.sh wikiProjects/myWikibase setup
```

Tarayıcıdan: [http://wb.local](http://wb.local)

---

## 🔗 Kaynaklar

* Orijinal proje: [Wikibase4Research](https://gitlab.com/nfdi4culture/wikibase4research/wikibase4research)
* Dokümantasyon ve hata çözümü: [Issues (error etiketi)](https://gitlab.com/nfdi4culture/wikibase4research/wikibase4research/-/issues/?label_name%5B%5D=error)