<?php
# Load EntitySchema extension
wfLoadExtension('EntitySchema');

# Configure EntitySchema settings
$wgEntitySchemaNamespace = 640;  # Default namespace for EntitySchema
$wgNamespacesToBeSearchedDefault[640] = true;  # Make EntitySchema searchable by default

# Grant permissions for EntitySchema
$wgGroupPermissions['*']['entity-schema-edit'] = true;  # Allow all users to edit schemas
$wgGroupPermissions['*']['entity-schema-restore'] = false;  # Only admins can restore schemas
$wgGroupPermissions['sysop']['entity-schema-restore'] = true;

# Define EntitySchema ID pattern
$wgEntitySchemaIdPattern = 'E[1-9][0-9]*';

# Maximum length for schema text
$wgEntitySchemaSchemaTextMaxLength = 50000;
?>