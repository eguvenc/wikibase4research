<?php
# Load Babel extension
wfLoadExtension('Babel');

# Configure Babel settings
$wgBabelCategoryNames = [
    'en' => 'User en',
    'de' => 'User de',
    'fr' => 'User fr',
    'es' => 'User es',
    'it' => 'User it'
];

# Enable Babel AutoCreate
$wgBabelUseDatabase = true;

# Configure Babel database for language information
$wgBabelCentralDb = false;

# Set language categories to create
$wgBabelMainCategory = 'User_$1';
$wgBabelCategorizeNamespaces = [NS_USER, NS_USER_TALK];
?>