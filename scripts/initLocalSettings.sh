#!/bin/bash

# ######################################################
# extend LocalSettings.php with active extension files
########################################################
echo "init LocalSettings based on active extensions..."
set -e

# Paths
local_settings_file="./LocalSettings.php"
directory="./LocalSettings.d"
json_file="./extensionManagement.json"


# Temporary file to store the include statements
temp_file="./temp_includes.php"

# Create or clear the temp file
: > "$temp_file"

# Function to append include statements based on active extensions and skins
append_includes() {
    local directory="$1"

    # Loop through the files in the LocalSettings.d directory
    for file in "$directory"/*.php; do
        # Extract the base filename without path and extension (e.g., "00_Wikibase")
        local base_filename=$(basename "$file" .php)

        # Extract the extension name from the filename (e.g., "Wikibase" from "00_Wikibase")
        local extension_name=$(echo "$base_filename" | sed -e 's/^[0-9]*_//')

        # Check in JSON if the extension is active
        is_active=$(jq -r --arg name "$extension_name" '
            .extensions.composer[$name].active //
            .extensions.download[$name].active //
            .extensions.git[$name].active //
            .skins.composer[$name].active //
            .skins.git[$name].active //
            .config_files[$name].active //
            false' "$json_file")

        if [ "$is_active" == "true" ]; then
            echo "Appending include for $file"

            echo "include_once '$file';" >> "$temp_file"
        else
            echo "Skipping $file as it is not active in the JSON configuration."
        fi
    done
}

# Append includes for extensions, skins, and config files
append_includes "$directory"

# Backup the original LocalSettings.php
cp "$local_settings_file" "${local_settings_file}.bak"

# Append the includes from the temp file to LocalSettings.php
cat "$temp_file" >> "$local_settings_file"

# Clean up the temporary file
rm "$temp_file"

echo "Update complete. Backed up original LocalSettings.php as ${local_settings_file}.bak"
