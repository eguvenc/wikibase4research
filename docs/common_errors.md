# MediaWiki and Extensions Error Troubleshooting Guide

## Error: Class "Onoi\MessageReporter\ObservableMessageReporter" Not Found

**Stacktrace:**
Occurs in `DatabaseSchemaUpdater.php(186)`.

**Reason:**
Wikibase (or another extension) is installed via git, but composer is not configured to include it in the dependency calculation.

**Solution:**
Include `extension.json` in `composer.local.json`:

```json
{
    "extra": {
        "merge-plugin": {
            "include": [
                "extensions/Wikibase/composer.json",
                "skins/*/composer.json"
            ]
        }
    }
}
```

---

## Error: com.fasterxml.jackson.core.JsonParseException

**Info:**
Unexpected character ('<' (code 60)) expected a valid value.

**Reason:**
Incorrect hardcoded mediawiki action API endpoint in WDQS image.

**Solution:**
1. Create a `.htaccess` to redirect `/w/api.php` to `/api.php`:

   ```
   RewriteEngine On
   RewriteRule ^w/api\.php$ /api.php [L,R=301]
   ```

2. In `docker-compose`, define a network alias to allow WDQS to connect to the defined `WIKIBASE_HOST`.

---

## RDF Store Reports the Last Update Time is Before the Minimum Safe Poll Time

**Reason:**
Empty database.

**Solution:**
Run the command: `/runUpdate.sh -- --start 20240813010000 --init -DwikibaseMaxDaysBack=999`.

---

## MediaWiki: Admin User is Renamed After Installation

**Reason:**
The name provided in `install.php` is either overwritten or compromised, possibly due to invalid formatting.

**Solution:**
Ensure that usernames are valid. For example, a username starting with a lowercase letter will not work and may be automatically replaced. Use a valid admin username that starts with a capital letter, such as "Admin".

---

## Error: Unable to Write File in Widgets Extension

**Reason:**
Insufficient file permissions for the web server user (`www-data`).

**Solution:**
Set the correct permissions for the Widgets compiled templates directory to allow the web server user to write:

```bash
chown -R www-data:www-data /var/www/html/extensions/Widgets/compiled_templates
chmod -R 755 /var/www/html/extensions/Widgets/compiled_templates
```

---

## Error: ContentHandler 'wikibase-property' Not Available

**Command:**
Occurs when running `maintenance/importDump.php`.

**Reason:**
SemanticWikibase is removing the registered contentHandlers for Wikibase.

**Solution:**
Add properties via script before using `importDump.php`.

---

## Error: Class XXX Not Found (After Adding an Extension)

**Reason:**
The extension may require additional dependencies that are not installed.

**Solution:**
Include the new extension folder in `composer.local.json`:

```json
{
    "extra": {
        "merge-plugin": {
            "include": [
                "extensions/Wikibase/composer.json",
                "extensions/<TheNewExtension>/composer.json",
                "skins/*/composer.json"
            ]
        }
    }
}
```

---

## Warning: session_name(): Session Name Cannot Be Changed

**Reason:**
`LocalSettings.php` contains a byte-mark, or an included PHP file is missing `<?php`.

**Solution:**
Add `<?php` to the first line of all included PHP files.

---

## Error: Class 'smarty' Not Found

**Reason:**
Widget is installed via git and is missing dependencies.

**Solution:**
Include the widgets extension folder in `composer.local.json`:

```json
{
    "extra": {
        "merge-plugin": {
            "include": [
                "extensions/Wikibase/composer.json",
                "extensions/Widgets/composer.json",
                "skins/*/composer.json"
            ]
        }
    }
}
```

---

## Error: undefined Method SMW_DI_Blob->getLabel()

**Reason:**
SRF Timeline cannot handle SMW subobjects.

**Solution:**
Modify `SRF_Timeline.php`:

```php
if ($dataValue == '') {
    $date_value = null;
} else if ($dataValue instanceof SMW_DI_Property) {
    $date_value = $dataValue->getDataItem()->getLabel();
}
```

---

## Error: Class "DataValues\Deserializers\DataValueDeserializer" Not Found

**Stacktrace:**
Occurs in `WikibaseRepo.ServiceWiring.php`.

**Reason:**
Missing dependencies.

**Solution:**
Include the necessary extension folder in `composer.local.json`.

---

## Exception: Unrecognized Statement in WDQS Update

**Reason:**
Incorrect URL or language settings in WDQS.

**Solution:**
Change wiki language to "en" by setting `$wgLanguageCode = "en"` in `LocalSettings.php`.

---

## Error: XXX is Not Compatible with the Current MediaWiki Core

**Reason:**
1. No version given in `extensionManagement.json`.
2. Syntax error in `LocalSettings.php`.

**Solution:**
1. Add version in `extensionManagement.json`.
2. Check syntax of `LocalSettings.php` (ensure it starts with `<?php`).
