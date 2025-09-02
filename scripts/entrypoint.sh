#!/bin/bash

# Check if MediaWiki is already installed
if [ ! -f /var/www/html/LocalSettings.php ]; then
  echo "LocalSettings.php not found, running installation..."
  # Run the MediaWiki installation
  php /var/www/html/maintenance/install.php \
    "${W4R_MW_WIKI_NAME}" \
    "${W4R_MW_ADMIN_USER}" \
    --pass "${W4R_MW_ADMIN_PASS}" \
    --server "${W4R_FULL_SERVER_NAME}" \
    --scriptpath "/w" \
    --dbserver "${W4R_DB_SERVER}" \
    --dbname "${W4R_DB_NAME}" \
    --dbuser "${W4R_DB_USER}" \
    --dbpass "${W4R_DB_PASS}"

  # run script to import content to wiki (images, pagedumps, fonts, etc)
  echo "importWikiContent..."
  # delete main page otherwise it cannot be imported
  echo "Main Page" > pages-to-delete.txt
  php maintenance/deleteBatch.php --r "deleted to prepare page import" pages-to-delete.txt
  bash ./scripts/importWikiContent.sh

else
  echo "LocalSettings.php found, skipping installation."
fi

#check first if symlink w exists
if [ -L /var/www/html/w ]; then
  echo "symlink w exists"
else
  echo "symlink w does not exist, creating"
  ln -s /var/www/html /var/www/html/w
fi

# Change the rights, to allow rest.php api calls and avoid 403
chmod 755 /var/www/html/w

#copy downloaded extensions from tmp to www folder
cp -r /var/tmp/extensions/* /var/www/html/extensions/
cp -r /var/tmp/skins/* /var/www/html/skins/
cp -r /var/tmp/composer.local.json /var/www/html/


# install dependencies
composer update

# Copy the generated LocalSettings.php
cp /var/tmp/extensionManagement.json /var/www/html/
cp /var/www/html/LocalSettings.php.tmp /var/www/html/LocalSettings.php
bash ./scripts/initLocalSettings.sh

# Parse the JSON and execute the maintenance scripts for extensions
json_file="./extensionManagement.json"
echo "Execute maintenance scripts, defined in extensionManagement.json"
jq -r '
    (.extensions.composer[]?, .extensions.git[]?) |
    select(.active == true) |
    select(.maintenance_scripts != null and .maintenance_scripts != "") |
    .maintenance_scripts' "$json_file" | while read -r script; do
    echo "Executing: $script"
    eval "$script"
done

echo "All maintenance scripts have been executed."

# run mediawiki update script
echo "run maintenance script: update.php"
php /var/www/html/maintenance/update.php --quick

# for testing purposes create another admin user
#php /var/www/html/maintenance/createAndPromote.php ${W4R_MW_ADMIN_USER} ${W4R_MW_ADMIN_PASS} --sysop --bureaucrat --force --interface-admin



exec apache2-foreground
