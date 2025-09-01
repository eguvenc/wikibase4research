<?php
# Load WikibaseEdtf extension
wfLoadExtension('WikibaseEdtf');

# Enable EDTF data type
$wgWBRepoSettings['entityTypes']['property']['datatypes'][] = 'edtf';
?>