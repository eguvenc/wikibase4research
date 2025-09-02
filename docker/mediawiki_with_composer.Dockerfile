ARG W4R_INIT_FOLDER=$W4R_INIT_FOLDER
ARG W4R_MW_VERSION=$W4R_MW_VERSION
ARG W4R_MW_WIKI_NAME=$W4R_MW_WIKI_NAME
ARG W4R_MW_ADMIN_USER=$W4R_MW_ADMIN_USER
ARG W4R_MW_ADMIN_PASS=$W4R_MW_ADMIN_PASS
ARG W4R_FULL_SERVER_NAME=$W4R_FULL_SERVER_NAME
ARG W4R_DB_SERVER=$W4R_DB_SERVER
ARG W4R_DB_NAME=$W4R_DB_NAME
ARG W4R_DB_USER=$W4R_DB_USER
ARG W4R_DB_PASS=$W4R_DB_PASS

FROM mediawiki:${W4R_MW_VERSION}

# bring argument into image
ARG W4R_INIT_FOLDER
ARG W4R_MW_WIKI_NAME
ARG W4R_MW_ADMIN_USER
ARG W4R_MW_ADMIN_PASS
ARG W4R_FULL_SERVER_NAME
ARG W4R_DB_SERVER
ARG W4R_DB_NAME
ARG W4R_DB_USER
ARG W4R_DB_PASS

# set env var from arg for use in scripts
ENV W4R_INIT_FOLDER=$W4R_INIT_FOLDER
ENV W4R_MW_WIKI_NAME=$W4R_MW_WIKI_NAME
ENV W4R_MW_ADMIN_USER=$W4R_MW_ADMIN_USER
ENV W4R_MW_ADMIN_PASS=$W4R_MW_ADMIN_PASS
ENV W4R_FULL_SERVER_NAME=$W4R_FULL_SERVER_NAME
ENV W4R_DB_SERVER=$W4R_DB_SERVER
ENV W4R_DB_NAME=$W4R_DB_NAME
ENV W4R_DB_USER=$W4R_DB_USER
ENV W4R_DB_PASS=$W4R_DB_PASS

# install jq and imagemagick
RUN apt-get update && apt-get install -y jq zip tar unzip libzip-dev imagemagick \
    && docker-php-ext-install zip

# copy extension scripts
COPY $W4R_INIT_FOLDER/config/LocalSettings.d /var/www/html/LocalSettings.d
COPY $W4R_INIT_FOLDER/config/composer.local.json /var/tmp/
COPY $W4R_INIT_FOLDER/config/extensionManagement.json /var/tmp/
COPY $W4R_INIT_FOLDER/dump.xml /var/www/html/dump.xml
COPY scripts/install-extensions.sh .
COPY scripts/jobrunner-entrypoint.sh /jobrunner-entrypoint.sh
COPY scripts/initLocalSettings.sh .
COPY scripts/patchSMWNamespaceManager.sh .
COPY scripts/rebuildWikibaseIdCounters.sql .

RUN chmod +x /jobrunner-entrypoint.sh
RUN chmod +x /var/www/html/initLocalSettings.sh
RUN chown -R www-data:www-data /var/www/html/dump.xml # set user so we are able to dump into these files

# Install composer
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
RUN composer self-update 2.1.14

# check if compers.json is there if yes chown to curr owner
RUN if [ -f /var/www/html/composer.json ]; then chown -R www-data:www-data /var/www/html/composer.json; fi
RUN chmod +x /var/www/html/install-extensions.sh
RUN bash install-extensions.sh

# now install the composer packages by require them via script
# RUN --mount=type=cache,target=/root/.composer/cache composer update


# Dump autoload
RUN composer dump-autoload

# Copy the entrypoint script into the Docker image
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh

# Set the entrypoint script as executable
RUN chmod +x /usr/local/bin/entrypoint.sh
