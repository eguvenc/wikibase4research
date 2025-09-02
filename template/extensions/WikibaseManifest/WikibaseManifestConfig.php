<?php
# Load WikibaseManifest extension
wfLoadExtension('WikibaseManifest');

# Configure Wikibase manifest settings
$wgWikibaseManifestEquivEntitiesProperties = [
    'P1' => 'http://www.wikidata.org/entity/P1628',  # Equivalent property
    'P2' => 'http://www.wikidata.org/entity/P2888',  # Exact match
];

$wgWikibaseManifestExternalServiceMapping = [
    'queryservice_ui' => 'http://query.' . getenv('W4R_SERVER_NAME'),
    'query_endpoint' => 'http://query.' . getenv('W4R_SERVER_NAME') . '/sparql'
];

?>