#!/bin/bash

# Define variables
IMPORT_DIR="/var/tmp/wikiPresets"
WWW_HTML_DIR="/var/www/html"
IMAGES_IMPORT_DIR="$IMPORT_DIR/images/import"
IMAGES_COPY_DIR="$IMPORT_DIR/images/copy"
FONTS_DIR="$IMPORT_DIR/fonts"
IMAGES_DEST_DIR="$WWW_HTML_DIR/images"
FONTS_DEST_DIR="$WWW_HTML_DIR/resources"
OWNER="www-data"
GROUP="www-data"
MODE="0755"
LOG_FILE="/var/log/wiki_import.log"

# Create log file
touch $LOG_FILE

echo "Script started at $(date)" | tee -a $LOG_FILE

# Check if the import directory exists and is not empty
if [ ! -d "$IMPORT_DIR" ] || [ -z "$(ls -A $IMPORT_DIR)" ]; then
  echo "Import directory $IMPORT_DIR does not exist or is empty. Exiting." | tee -a $LOG_FILE
  exit 1
fi

# Find all files in the xml pages import directory
if [ -d "$IMPORT_DIR/pages/xml" ]; then
  found_files=($(find $IMPORT_DIR/pages/xml -type f))
  if [ ${#found_files[@]} -eq 0 ]; then
    echo "No files found in $IMPORT_DIR/pages/xml. Skipping page imports." | tee -a $LOG_FILE
  else
    # Run importSites maintenance script for each (wikipages) dump file
    for file in "${found_files[@]}"; do
      echo "Importing $file" | tee -a $LOG_FILE
      php $WWW_HTML_DIR/maintenance/importDump.php < "$file"
    done
  fi
else
  echo "Pages directory $IMPORT_DIR/pages/xml does not exist. Skipping page imports." | tee -a $LOG_FILE
fi

# Find all files in the text pages import directory
if [ -d "$IMPORT_DIR/pages/txt" ]; then
  found_files=($(find $IMPORT_DIR/pages/txt -type f))
  if [ ${#found_files[@]} -eq 0 ]; then
    echo "No files found in $IMPORT_DIR/pages/txt. Skipping page imports." | tee -a $LOG_FILE
  else
    # Run importSites maintenance script for all (wikipages) dump file
    echo "Importing $file" | tee -a $LOG_FILE
    php $WWW_HTML_DIR/maintenance/importTextFiles.php $IMPORT_DIR/pages/txt/*
  fi
else
  echo "Pages directory $IMPORT_DIR/pages/txt does not exist. Skipping page imports." | tee -a $LOG_FILE
fi

# Run importImages maintenance script if directory exists
if [ -d "$IMAGES_IMPORT_DIR" ] && [ -n "$(ls -A $IMAGES_IMPORT_DIR)" ]; then
  echo "Running importImages script" | tee -a $LOG_FILE
  php $WWW_HTML_DIR/maintenance/importImages.php $IMAGES_IMPORT_DIR
else
  echo "Import images directory $IMAGES_IMPORT_DIR does not exist or is empty. Skipping image imports." | tee -a $LOG_FILE
fi

# Copy specified dump images into installation if directory exists and is not empty
if [ -d "$IMAGES_COPY_DIR" ] && [ -n "$(ls -A $IMAGES_COPY_DIR)" ]; then
  echo "Copying images" | tee -a $LOG_FILE
  cp -R $IMAGES_COPY_DIR/* $IMAGES_DEST_DIR
  chown -R $OWNER:$GROUP $IMAGES_DEST_DIR
  chmod -R $MODE $IMAGES_DEST_DIR
else
  echo "Copy images directory $IMAGES_COPY_DIR does not exist or is empty. Skipping image copy." | tee -a $LOG_FILE
fi

# Copy fonts into installation if directory exists and is not empty
if [ -d "$FONTS_DIR" ] && [ -n "$(ls -A $FONTS_DIR)" ]; then
  echo "Copying fonts" | tee -a $LOG_FILE
  cp -R $FONTS_DIR/* $FONTS_DEST_DIR
  chown -R $OWNER:$GROUP $FONTS_DEST_DIR
  chmod -R $MODE $FONTS_DEST_DIR
else
  echo "Fonts directory $FONTS_DIR does not exist or is empty. Skipping fonts copy." | tee -a $LOG_FILE
fi

# Execute runJobs maintenance script
echo "Running runJobs script" | tee -a $LOG_FILE
php $WWW_HTML_DIR/maintenance/runJobs.php



echo "Script finished at $(date)" | tee -a $LOG_FILE
