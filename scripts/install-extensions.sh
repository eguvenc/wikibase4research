#!/bin/bash

set -e

#Function to download extension via url
download_extension(){
    local type="$1"
    local path="$2"
    local custom_name="$4"
    local post_cmd="$5"

    local dirname="$type"
    echo "Download $path into folder '$dirname'"
    cd $dirname
    if [ "$custom_name" != "" ]; then
        echo "Using custom folder: $custom_name !"
        echo "This is the download command: curl -L -o $custom_name $path"
        curl -L -o "$custom_name" "$path"
    else
        echo "This is the download command: curl -L -O $path"
        curl -L -O "$path"
    fi

    if [ "$post_cmd" != "null" ]; then
        echo "execute cmd_after_install: $post_cmd"
        eval "$post_cmd"
    fi
    cd -
}


# Function to install git extensions
install_git_extension() {
    local type="$1"
    local path="$2"
    local version="$3"
    local custom_name="$4"
    local post_cmd="$5"

    local dirname="$type"
    echo "Installing $path:$version into folder '$dirname'"
    cd $dirname
    local branch=""
    if [ "$version" != "" ]; then
        branch="-b $version"
        echo "Using branch: $branch"
    fi
    if [ "$custom_name" != "" ]; then
        echo "Using custom name: $custom_name !"
        echo "This is the clone command: git clone $path $branch $custom_name --recurse-submodules"
        git clone "$path" $branch "$custom_name" --recurse-submodules
    else
        echo "This is the clone command: git clone $path $branch --recurse-submodules"
        git clone "$path" $branch --recurse-submodules
    fi

    if [ "$post_cmd" != "null" ]; then
        echo "execute cmd_after_install: $post_cmd"
        eval "$post_cmd"
    fi
    cd -
}

# Function to install composer extensions
install_composer_extensions() {
    local packages="$1"
    if [ ! -z "$packages" ]; then
        echo "Installing $packages"
        composer require $packages --no-update
    fi
    #composer update
}

# Parse JSON file and install extensions and skins
json_file="/var/tmp/extensionManagement.json"
packages=""


mkdir /var/tmp/extensions
# Install extensions (composer and git)
extensions=$(jq -c '.extensions | to_entries[]' "$json_file")
while IFS= read -r entry; do
    source=$(echo "$entry" | jq -r '.key')
    items=$(echo "$entry" | jq -c '.value | to_entries[]')
    while IFS= read -r item; do
        name=$(echo "$item" | jq -r '.key')
        path=$(echo "$item" | jq -r '.value.path')
        version=$(echo "$item" | jq -r '.value.version')
        custom_name=$(echo "$item" | jq -r '.value.custom_folder')
        active=$(echo "$item" | jq -r '.value.active')
        post_cmd=$(echo "$item" | jq -r '.value.cmd_after_install')

        if [ "$active" == "true" ]; then
            if [ "$source" == "composer" ]; then
                packages="$packages $path:$version"
                echo "Mark $name for composer: $packages"
            elif [ "$source" == "git" ]; then
                install_git_extension "/var/tmp/extensions" "$path" "$version" "$custom_name" "$post_cmd"
            elif [ "$source" == "download" ]; then
                download_extension "/var/tmp/extensions" "$path" "$version" "$custom_name" "$post_cmd"
            fi
        fi
    done <<< "$items"
done <<< "$extensions"

# Install skins (composer and git)
mkdir /var/tmp/skins
skins=$(jq -c '.skins | to_entries[]' "$json_file")
while IFS= read -r entry; do
    source=$(echo "$entry" | jq -r '.key')
    items=$(echo "$entry" | jq -c '.value | to_entries[]')
    while IFS= read -r item; do
        name=$(echo "$item" | jq -r '.key')
        path=$(echo "$item" | jq -r '.value.path')
        version=$(echo "$item" | jq -r '.value.version')
        custom_name=$(echo "$item" | jq -r '.value.custom_folder')
        active=$(echo "$item" | jq -r '.value.active')
        post_cmd=$(echo "$item" | jq -r '.value.cmd_after_install')

        if [ "$active" == "true" ]; then
            if [ "$source" == "composer" ]; then
                packages="$packages $path:$version"
                echo "Mark $name for composer: $packages"
            elif [ "$source" == "git" ]; then
                install_git_extension "/var/tmp/skins" "$path" "$version" "$custom_name" "$post_cmd"
            fi

        fi
    done <<< "$items"
done <<< "$skins"

# Install composer extensions
echo "Composer install: $packages"
install_composer_extensions "$packages"
