-- By Jeroen De Dauw / https://Professional.Wiki
-- License: GPL-2.0-or-later
-- copied from https://gist.github.com/JeroenDeDauw/c86a5ab7e2771301eb506b246f1af7a6#file-rebuildwikibaseidcounters-sql
-- see: https://wikibase.consulting/transferring-wikibase-data-between-wikis/
-- this script is to activate "create new item" function after importing a wikibase xml dump

SELECT * FROM /*_*/wb_id_counters;

REPLACE INTO /*_*/wb_id_counters VALUE((SELECT COALESCE(MAX(CAST(SUBSTRING(`page_title`, 2) AS UNSIGNED)), 0) FROM `page` WHERE `page_namespace` = 120), 'wikibase-item');

REPLACE INTO /*_*/wb_id_counters VALUE((SELECT COALESCE(MAX(CAST(SUBSTRING(`page_title`, 2) AS UNSIGNED)), 0) FROM `page` WHERE `page_namespace` = 122), 'wikibase-property');

SELECT * FROM /*_*/wb_id_counters;