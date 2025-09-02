<?php
# 30_WikibaseSettings.php


# Semantic Wikibase configuration
wfLoadExtension('SemanticWikibase');

# Wikibase and SMW both define the namespace "property" we need to rename one of the namespaces

#OPTION A) rename wikibase property namespace (this will lead to problems when importing properties from xml dump or within wdqs-updater)
#$wgExtraNamespaces[WB_NS_PROPERTY] = 'WikibaseProperty';
#$wgExtraNamespaces[WB_NS_PROPERTY_TALK] = 'WikibaseProperty_talk';

#$wgHooks['CanonicalNamespaces'][] = static function (&$list) {
#    global $wgExtraNamespaces;
#    $wgExtraNamespaces[WB_NS_PROPERTY] = $list[WB_NS_PROPERTY] = 'Wikibase_property';
#    $wgExtraNamespaces[WB_NS_PROPERTY_TALK] = $list[WB_NS_PROPERTY_TALK] = 'Wikibase_property_talk';
#};

#OPTION B) rename SMW property namespace (needs patching of extensions/SemanticMediaWiki&src/NamespaceManager.php see scripts/patchSMWNamespaceManager.sh for details)
$wgExtensionFunctions[] = function() {
    $GLOBALS['wgExtraNamespaces'][SMW_NS_PROPERTY] = 'SMWProperty';
    $GLOBALS['wgExtraNamespaces'][SMW_NS_PROPERTY_TALK] = 'SMWProperty_talk';
};

$wgHooks['CanonicalNamespaces'][] = static function (&$list) {
    global $wgExtraNamespaces;
    $wgExtraNamespaces[SMW_NS_PROPERTY] = $list[SMW_NS_PROPERTY] = 'SMWProperty';
    $wgExtraNamespaces[SMW_NS_PROPERTY_TALK] = $list[SMW_NS_PROPERTY_TALK] = 'SMWProperty_talk';
};

# now activate SMW (have to be disabled in SMW config file to work properly) 
wfLoadExtension('SemanticMediaWiki');
enableSemantics(getenv('W4R_SERVER_NAME'));
# end of property renaming

$wgGroupPermissions['user']['item-create'] = true;
$wgGroupPermissions['user']['property-create'] = true;
$wgSemanticWikibaseLanguage = 'de';
$smwgNamespacesWithSemanticLinks[WB_NS_PROPERTY] = true;
$smwgNamespacesWithSemanticLinks[WB_NS_ITEM] = true;



