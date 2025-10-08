
## Fixing permission errors:

1. Install ACL for Ubuntu

```bash
sudo apt install acl
```

2. Add write permissions to MediaWiki components for your user e.g. `ersin`:

```bash
sudo setfacl -R -m u:ersin:rwx /var/www/mediawiki
```

3. Write permission for the web server (`www-data`):

```bash
sudo setfacl -R -m u:www-data:rwx /var/www/mediawiki
```

4. Ensure that newly created files and folders have the same permissions as the ACL:

```bash
sudo setfacl -R -d -m u:ersin:rwx /var/www/mediawiki
sudo setfacl -R -d -m u:www-data:rwx /var/www/mediawiki
```