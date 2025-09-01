<?php
# Load OAuth extension
wfLoadExtension('OAuth');

# Configure OAuth settings
$wgOAuthSecretKey = 'secret';  # This should be changed in production
$wgOAuthEnableOAuthExt = true;

# Configure OAuth endpoints
$wgOAuthRedirectUri = 'http://' . getenv('W4R_SERVER_NAME') . '/oauth/callback';

# Set up OAuth database
$wgOAuthDBname = 'my_wiki';  # Use the same database as your wiki
$wgOAuthDBTablePrefix = 'oauth_';

# OAuth consumer settings
$wgOAuthGroupsToNotify = ['sysop'];  # Notify admins of new OAuth consumers
$wgMWOAuthSecureTokenTransfer = true;  # Use HTTPS for token transfer
$wgOAuthSecretKey = getenv('OAUTH_SECRET_KEY') ?: 'default-secret-key';

# OAuth consumer limits
$wgOAuthConsumerPermissions = [
    'basic' => [
        'grants' => ['basic'],
        'required' => true
    ],
    'mwoauth-authonly' => [
        'grants' => ['mwoauth-authonly'],
        'required' => false
    ],
    'mwoauth-authonlyprivate' => [
        'grants' => ['mwoauth-authonlyprivate'],
        'required' => false
    ]
];

# Allow administrators to manage OAuth consumers
$wgGroupPermissions['sysop']['mwoauthmanageconsumer'] = true;
$wgGroupPermissions['sysop']['mwoauthviewprivate'] = true;
$wgGroupPermissions['sysop']['mwoauthupdateownconsumer'] = true;

# OAuth client settings
$wgOAuthClientId = getenv('OAUTH_CLIENT_ID') ?: '';
$wgOAuthClientSecret = getenv('OAUTH_CLIENT_SECRET') ?: '';

?>