
# Wikibase4Research – Türkçe Kurulum Rehberi

Wikibase4Research, Docker Compose kullanarak **MediaWiki**, **SemanticMediaWiki (SMW)**, **Wikibase** veya **SemanticWikibase** sistemlerini; seçili eklentilerle birlikte kolayca ayağa kaldırmanı sağlar.  
Tüm işlemler `wiki.sh` komut dosyası ile yönetilir.

---

## 🚀 Önkoşullar

- **Docker** ve **Docker Compose v2**  
- **Git**

Ubuntu/Debian için:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker $USER
newgrp docker
````

---

## 📥 Depoyu Klonla

```bash
git clone https://gitlab.com/nfdi4culture/wikibase4research/wikibase4research.git
cd wikibase4research
```

Projen için bir klasör oluştur:

```bash
mkdir -p wikiProjects/myProject
cp -r wikiPresets/wikibase_plain/* wikiProjects/myProject
git -C wikiProjects/myProject init
```

---

## ⚙️ .env Dosyası

Örnek dosyayı kopyala:

```bash
cp wikiProjects/myProject/config/.env.template wikiProjects/myProject/config/.env
```

**Önemli ayarlar:**

* `W4R_MW_VERSION="1.39"` – MediaWiki sürümü
* `W4R_MW_WIKI_NAME="MyWiki"` – Site adı
* `W4R_MW_ADMIN_USER="Admin"` / `W4R_MW_ADMIN_PASS="changeme123"` – Yönetici hesabı
* `W4R_SERVER_NAME="wb.local"` – Host adı
* `W4R_INIT_FOLDER="./wikiProjects/myProject"` – Proje klasörünü işaret etmeli
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
./wiki.sh wikiProjects/myProject setup
```

Alternatif:

```bash
./wiki.sh wikiProjects/myProject up --build -d
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
Varsayılan: **Admin / changeme123**

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
./wiki.sh wikiProjects/myProject munge
```

TTL dosyası eklemek için:

```bash
./wiki.sh wikiProjects/myProject addttl path/to/file.ttl
```

---

## 💾 İçerik Yedekleme ve Geri Yükleme

**XML Dump:**

```bash
./wiki.sh wikiProjects/myProject exportdump
./wiki.sh wikiProjects/myProject importdump
```

**MySQL Dump:**

```bash
./wiki.sh wikiProjects/myProject mysqldump
./wiki.sh wikiProjects/myProject importmysqldump export/YYYY-MM-DD.sql
```

**Tüm paket:**

```bash
./wiki.sh wikiProjects/myProject export
./wiki.sh wikiProjects/myProject export-small
```

> Not: Görseller `wb_resources/images/` klasöründe tutulur, ayrıca kopyalanmalıdır.

---

## 🔄 Güncelleme & Kaldırma

* Güncelle:

```bash
./wiki.sh wikiProjects/myProject update
```

* Kaldır (tüm veriler silinir):

```bash
./wiki.sh wikiProjects/myProject remove
```

---

## 🔧 Faydalı Komutlar

* Container içinde komut çalıştır:

  ```bash
  ./wiki.sh wikiProjects/myProject command "php maintenance/runJobs.php"
  ```

* Dosya izinlerini düzelt:

  ```bash
  ./wiki.sh wikiProjects/myProject fixpermissions
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