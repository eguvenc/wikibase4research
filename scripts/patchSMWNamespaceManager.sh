#!/bin/sh

# SMW and Wikibase define the same namespace 'property' we need to rename one of these to avoid errors.
# but changing the wikibase namespace leads to problems with importing properties from dump and wdqs-updater
# In order to rename the SMW property namespace we also need to patch the NamespaceManager.php as the namespace canonicalNames are hardcoded there
# if we dont change them, the Wikibase Namespace will be automatically be removed by SMW and we wil get an AssertionException when creating a wikibase property (BadPageTitle)

# Define the file path
FILE="extensions/SemanticMediaWiki/src/NamespaceManager.php"

# Check if the file exists
if [ -f "$FILE" ]; then
    # Use sed to replace 'property' with 'SMWProperty' in the file
    sed -i "s/'Property'/'SMWProperty'/g" "$FILE"
    sed -i "s/'Property_talk'/'SMWProperty_talk'/g" "$FILE"
    echo "Replacement completed successfully."
else
    echo "File not found: $FILE"
fi