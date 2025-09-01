# Function to build and start containers with an optional second parameter

# Help text function
show_help() {
    echo "Usage: $0 [OPTIONS] PRESET_FOLDER ACTION [ARGS...]
       $0 init

Arguments:
  PRESET_FOLDER   The folder containing your preset configuration files.
  ACTION          The action to perform (see actions below).
  ARGS...         Additional arguments for specific actions.

Options:
  -p, --project-name NAME   Specify the Docker Compose project name. If not provided,
                           a default name based on PRESET_FOLDER will be used.
  -h, --help               Show this help message and exit.

Actions:
  setup           Build and start containers using the specified preset.
  update          Update MediaWiki containers without losing existing data.
  remove          Stop and remove containers and volumes (destructive - backup first!).
  exportdump      Export MediaWiki content to XML dump file.
  importdump      Import MediaWiki content from XML dump file.
  mysqldump       Create MySQL database backup to preset/dumps/ directory.
  importmysqldump Import MySQL database from backup file. Usage: ... importmysqldump DUMP_FILE
  mongodump       Create MongoDB database backup to directory. Usage: ... mongodump DUMP_DIR
  mongorestore    Import MongoDB database from dump directory. Usage: ... mongorestore DUMP_DIR
  munge           Generate RDF dump and load into SPARQL endpoint.
  addttl          Load TTL file into Blazegraph. Usage: ... addttl TTL_FILE
  checkuptime     Check container health and send email alerts if issues found.
  testmail        Test email notification configuration.
  command         Execute command in wikibase container. Usage: ... command \"COMMAND\"
  init            Initialize new Wikibase4Research configuration (run from root directory).
  export          Export both database dump and wb_resources files to export directory.
  export-small    Export database dump and wb_resources files with only smallest thumbnail images.
  import          Import database dump and wb_resources files from export directory.
  fixpermissions  Fix ownership permissions on wb_resources directory (useful after Docker operations).

  [docker-compose] Any docker-compose command (up, down, logs, ps, etc.).

Examples:
  $0 init
  $0 wikiPresets/myPreset setup
  $0 wikiPresets/myPreset mysqldump
  $0 wikiPresets/myPreset importmysqldump dumps/2024-01-15.sql
  $0 wikiPresets/myPreset addttl data/ontology.ttl
  $0 wikiPresets/myPreset logs
  $0 -p myproject wikiPresets/myPreset setup"
  $0 wikiPresets/myPreset export-small
}

# Initialize variables
projectName=""
presetFolder=""
action=""

# Parse options
while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--project-name)
            shift
            projectName="$1"
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        init)
            action="init"
            break
            ;;
        *)
            presetFolder="$1"
            action="$2"
            break
            ;;
    esac
    shift
done

# Check if action is provided
if [ -z "$action" ]; then
    show_help
    exit 1
fi

# Check if presetFolder is required for non-init actions
if [ "$action" != "init" ] && [ -z "$presetFolder" ]; then
    show_help
    exit 1
fi

# Generate default project name based on presetFolder param if not provided
if [ -z "$projectName" ]; then
    presetFolderDefault="${presetFolder/wikiPresets\//}"            # Remove default preset folder name
    presetFolderDefault="${presetFolderDefault//\//_}"              # Replace all / with _
    presetFolderDefault=$(echo "$presetFolderDefault" | tr '[:upper:]' '[:lower:]')   # Convert to lowercase
    presetFolderDefault=$(echo "$presetFolderDefault" | sed 's/^[^a-zA-Z0-9]*//')  # Remove leading non-alphanumeric characters
    presetFolderDefault="${presetFolderDefault%_}" # Remove trailing _ if it exists
    projectName="$presetFolderDefault"
fi

# Arg 1: env-file
build_compose_command() {
    local serviceList="$1"
    local service_cmd=""

    # Initialize the base command
    local compose_command="docker compose -p $projectName"

    # Convert the comma-separated list into an array
    IFS=',' read -r -a services <<< "$serviceList"

    # Iterate through the list and construct the command
    for service in "${services[@]}"; do
       service_cmd="$service_cmd -f compose-${service}.yml"
    done

    # Return the complete command
    echo "${compose_command} ${service_cmd}"
}

# Arg 1: presetFolder
get_env_file_from_preset() {
    local presetFolder="$1"

    # Check if presetFolder is empty, if so return nothing
    if [ -z "$presetFolder" ]; then
        return
    fi

    # Check for .env file, fallback to .env.template
    if [ -f "$presetFolder/config/.env" ]; then
        echo "$presetFolder/config/.env"
    else
        echo "$presetFolder/config/.env.template"
    fi
}

# Load env variables if presetFolder is not empty
if [ -n "$presetFolder" ]; then
    source "$(get_env_file_from_preset "$presetFolder")"
fi

send_alert_email() {
    local container_status="$1"
    echo "${W4R_SERVER_NAME}@tib.eu"
    echo "$container_status" | mailx \
        -r "${W4R_SERVER_NAME}@tib.eu" \
        -s "Wikibase Container Alert" \
        "${W4R_MW_ADMIN_EMAIL}"
}

# Handle the action parameter
case "$action" in
    setup)
        command=$(build_compose_command "${W4R_COMPOSER_SERVICE_INCLUDE}")
        if [ ! -f "$presetFolder/dump.xml" ]; then
            touch "$presetFolder/dump.xml"
        fi
        echo "Executing following command: $command --env-file $(get_env_file_from_preset "$presetFolder") up --build -d"
        $command --env-file "$(get_env_file_from_preset "$presetFolder")" up --build -d
        ;;
    update)
        command="docker compose -p $projectName -f compose-wiki.yml"
        $command --env-file "$(get_env_file_from_preset "$presetFolder")" start
        echo "Executing following command: $command --env-file $(get_env_file_from_preset "$presetFolder") build --no-cache wikibase "
        $command --env-file "$(get_env_file_from_preset "$presetFolder")" down wikibase reverse-proxy
        $command --env-file "$(get_env_file_from_preset "$presetFolder")" build --no-cache wikibase reverse-proxy
        $command --env-file "$(get_env_file_from_preset "$presetFolder")" up -d
        ;;
    remove)
        echo "****************************** WARNING **********************************"
        echo "* This command will delete ALL your wiki data (containers and volumes)! *"
        echo "* Run './wiki.sh <project_path> mysqldump' first , to save your data.   *"
        echo "* Are you sure you want to continue? Type 'delete' to confirm deletion. *"
        echo "****************************** WARNING **********************************"
        read user_input

        if [ "$user_input" == "delete" ]; then
            command=$(build_compose_command)
            echo "Executing following command: $command --env-file $(get_env_file_from_preset "$presetFolder") down -v"
            $command --env-file "$(get_env_file_from_preset "$presetFolder")" down -v
        else
            echo "Remove command aborted."
        fi

        ;;
    exportdump)
        # -u 1000 sets the user to the file owner
        command="docker compose -p $projectName exec -u 1000 wikibase bash -c \"php maintenance/dumpBackup.php --quiet --current --include-files --uploads > /var/www/html/dump.xml\""
        echo "Executing following command: $command"
        eval $command
        ;;
    importdump)
        # Check if dump file argument is provided
        dump_file="${3:-}"
        if [ -z "$dump_file" ]; then
            echo "Please provide the SQL dump file as an argument. You can find the dump file in the preset folder's dumps directory."
            echo "Usage: $0 <preset_folder> importdump <dump_file>"
            exit 1
        fi

        # Ensure the SQL dump file is available on the host
        if [ ! -f "$dump_file" ]; then
            echo "SQL dump file not found. Please ensure the file '$dump_file' exists."
            exit 1
        fi

        # Copy the SQL file into the container
        docker compose -p $projectName cp ./"$dump_file" database:/tmp/dump.sql

        # Extract MySQL credentials and perform database import
        MARIADB_USER=$(docker compose -p $projectName exec -T database env | grep MARIADB_USER | cut -d'=' -f2)
        MARIADB_PASSWORD=$(docker compose -p $projectName exec -T database env | grep MARIADB_PASSWORD | cut -d'=' -f2)
        MARIADB_DATABASE=$(docker compose -p $projectName exec -T database env | grep MARIADB_DATABASE | cut -d'=' -f2)

        # Perform the import
        import_command="mysql -u $MARIADB_USER -p$MARIADB_PASSWORD $MARIADB_DATABASE < /tmp/dump.sql"
        docker compose -p $projectName exec -T database bash -c "$import_command"

        echo "MySQL import completed."
        ;;
    mysqldump)
            # Create export directory in preset folder if it doesn't exist
            mkdir -p "$presetFolder/export"

            # Extract MySQL credentials and perform database dump
            MARIADB_USER=$(docker compose -p $projectName exec -T database env | grep MARIADB_USER | cut -d'=' -f2)
            MARIADB_PASSWORD=$(docker compose -p $projectName exec -T database env | grep MARIADB_PASSWORD | cut -d'=' -f2)
            MARIADB_DATABASE=$(docker compose -p $projectName exec -T database env | grep MARIADB_DATABASE | cut -d'=' -f2)

            # Create dump filename with timestamp
            DUMP_FILENAME="$(date +"%Y-%m-%d").sql"

            # Perform the mysqldump
            dump_command="mysqldump -u $MARIADB_USER -p$MARIADB_PASSWORD $MARIADB_DATABASE > /tmp/$DUMP_FILENAME"
            docker compose -p $projectName exec -T database bash -c "$dump_command"

            # Copy the SQL file back to the preset folder's export directory
            docker compose -p $projectName cp database:/tmp/$DUMP_FILENAME "$presetFolder/export/"

            echo "MySQL dump completed and saved to $presetFolder/export/$DUMP_FILENAME"
        ;;
    importmysqldump)
        # Check if dump file argument is provided
        dump_file="${3:-}"
        if [ -z "$dump_file" ]; then
            echo "Please provide the SQL dump file as an argument."
            echo "Usage: $0 <preset_folder> importmysqldump <dump_file>"
            exit 1
        fi

        # Ensure the SQL dump file is available on the host
        if [ ! -f "$dump_file" ]; then
            echo "SQL dump file not found. Please ensure the file '$dump_file' exists."
            exit 1
        fi

        # Copy the SQL file into the container
        docker compose -p $projectName cp ./"$dump_file" database:/tmp/import_dump.sql

        # Extract MySQL credentials and perform database import
        MARIADB_USER=$(docker compose -p $projectName exec -T database env | grep MARIADB_USER | cut -d'=' -f2)
        MARIADB_PASSWORD=$(docker compose -p $projectName exec -T database env | grep MARIADB_PASSWORD | cut -d'=' -f2)
        MARIADB_DATABASE=$(docker compose -p $projectName exec -T database env | grep MARIADB_DATABASE | cut -d'=' -f2)

        # Perform the import
        import_command="mysql -u $MARIADB_USER -p$MARIADB_PASSWORD $MARIADB_DATABASE < /tmp/import_dump.sql"
        docker compose -p $projectName exec -T database bash -c "$import_command"

        echo "MySQL import completed."
        ;;
    munge)
        # Steps for the munge operation
        command_wdqs="docker compose -p $projectName exec -T wdqs"

        rdf_dump_command="php ./extensions/Wikibase/repo/maintenance/dumpRdf.php --server ${W4R_FULL_SERVER_NAME} --output /tmp/rdfOutput"
        munge_command="./munge.sh -f /tmp/rdfOutput -d /tmp/mungeOut -- --conceptUri ${W4R_FULL_SERVER_NAME}"
        sparql_update_command="curl \"http://localhost:9999/bigdata/namespace/wdq/sparql\" --data-urlencode \"update=DROP ALL;\""
        load_data_command="./loadData.sh -n wdq -d /tmp/mungeOut"

        # Execute the commands in sequence
        echo "Generating RDF dump..."
        echo $rdf_dump_command
        docker compose -p $projectName exec -T wikibase sh -c "$rdf_dump_command"

        echo "Copy RDF dump to local filesystem..."
        docker compose -p $projectName cp wikibase:/tmp/rdfOutput ./rdfOutput

        echo "Copy RDF dump to wdqs container..."
        docker compose -p $projectName cp ./rdfOutput wdqs:/tmp/rdfOutput

        echo "Running munge command..."
        $command_wdqs sh -c "$munge_command"

        echo "Updating SPARQL endpoint..."
        $command_wdqs sh -c "$sparql_update_command"

        echo "Loading munged data into SPARQL endpoint..."
        $command_wdqs sh -c "$load_data_command"
        ;;
    command)
        command="docker compose -p $projectName exec -u 1000 wikibase bash -c \"${@:3}\""
        echo "Executing following command: $command"
        eval $command
        ;;
    checkuptime)
        # !!! NOT WORKING right now !!!
        # Display crontab command with absolute paths
        echo "To add to crontab for monitoring (e.g. every 5 minutes):"
        echo "*/5 * * * * $(which bash) $(readlink -f "$0") $presetFolder $action"
        echo "---"

        echo "Checking container statuses for project: $projectName"

        # Get container statuses
        container_status=$(docker compose -p $projectName ps | grep ${projectName})

        # Check each container's status
        problematic_containers=""
        healthy_containers=""
        while IFS= read -r line; do
            if [[ ! "$line" =~ "Up" && -n "$line" ]]; then
                echo "WARNING: Problematic container found: $line"
                problematic_containers+="$line"$'\n'
            else
                echo "Container healthy: $line"
                healthy_containers+="$line"$'\n'
            fi
        done <<< "$container_status"

        echo "---"
        echo "Status Summary:"
        echo "Healthy containers: $(($(echo "$healthy_containers" | wc -l) - 1))"
        echo "Problematic containers: $(($(echo "$problematic_containers" | wc -l) - 1))"

        # If there are problematic containers, send email
        if [ ! -z "$problematic_containers" ]; then
            echo "Sending alert email about problematic containers..."
            send_alert_email "$problematic_containers"
            echo "Alert email sent."
        else
            echo "All containers are running normally."
        fi
        ;;
    testmail)
        echo "Testing email configuration..."
        send_alert_email "test"
        echo "Test email sent. Please check your inbox."
        echo "If you don't receive the email, verify your mailx configuration and email variables."
        ;;
    addttl)
        # Check if .ttl file argument is provided
        ttl_file="${3:-}"
        if [ -z "$ttl_file" ]; then
            echo "Please provide the TTL file as an argument."
            echo "Usage: $0 <preset_folder> addttl <ttl_file>"
            exit 1
        fi

        # Ensure the TTL file is available on the host
        if [ ! -f "$ttl_file" ]; then
            echo "TTL file not found. Please ensure the file '$ttl_file' exists."
            exit 1
        fi

        # Get the filename without path
        ttl_filename=$(basename "$ttl_file")

        # Copy the TTL file into the container
        echo "Copying TTL file to wdqs container..."
        docker compose -p $projectName cp "$ttl_file" wdqs:/tmp/"$ttl_filename"

        # Execute the curl command to load the TTL file into Blazegraph
        echo "Loading TTL file into Blazegraph..."
        load_ttl_command="curl -D- -H 'Content-Type: text/turtle' --upload-file /tmp/$ttl_filename -X POST 'http://localhost:9999/bigdata/sparql'"
        docker compose -p $projectName exec -T wdqs bash -c "$load_ttl_command"

        echo "TTL file loaded into Blazegraph."
        ;;
    export)
        # Create export directory in preset folder if it doesn't exist
        mkdir -p "$presetFolder/export"

        # First perform database dump
        echo "Exporting database..."
        MARIADB_USER=$(docker compose -p $projectName exec -T database env | grep MARIADB_USER | cut -d'=' -f2)
        MARIADB_PASSWORD=$(docker compose -p $projectName exec -T database env | grep MARIADB_PASSWORD | cut -d'=' -f2)
        MARIADB_DATABASE=$(docker compose -p $projectName exec -T database env | grep MARIADB_DATABASE | cut -d'=' -f2)

        # Create dump filename with timestamp
        DUMP_FILENAME="$(date +"%Y-%m-%d").sql"

        # Perform the mysqldump
        dump_command="mysqldump -u $MARIADB_USER -p$MARIADB_PASSWORD $MARIADB_DATABASE > /tmp/$DUMP_FILENAME"
        docker compose -p $projectName exec -T database bash -c "$dump_command"

        # Copy the SQL file back to the preset folder's export directory
        docker compose -p $projectName cp database:/tmp/$DUMP_FILENAME "$presetFolder/export/"

        # Export wb_resources if it exists
        if [ -d "$presetFolder/wb_resources" ]; then
            echo "Exporting wb_resources..."
            # Create zip file with timestamp
            RESOURCES_ZIP="wb_resources_$(date +"%Y-%m-%d").zip"

            # Remove existing zip file if it exists
            if [ -f "$presetFolder/export/$RESOURCES_ZIP" ]; then
                echo "Removing existing zip file..."
                rm -f "$presetFolder/export/$RESOURCES_ZIP"
            fi

            # Create the zip file with error checking
            if (cd "$presetFolder" && zip -r "export/$RESOURCES_ZIP" wb_resources/); then
                echo "wb_resources exported to $presetFolder/export/$RESOURCES_ZIP"

                # Test the created zip file
                if ! unzip -t "$presetFolder/export/$RESOURCES_ZIP" >/dev/null 2>&1; then
                    echo "WARNING: Created zip file failed integrity test"
                    echo "Export may be incomplete or corrupted"
                fi
            else
                echo "ERROR: Failed to create wb_resources zip file"
                echo "Check if zip utility is installed and wb_resources directory is accessible"
                exit 1
            fi
        else
            echo "No wb_resources directory found in $presetFolder"
        fi

        echo "Export completed. Files saved to $presetFolder/export/"
        echo "Database dump: $presetFolder/export/$DUMP_FILENAME"
        if [ -d "$presetFolder/wb_resources" ]; then
            echo "Resources: $presetFolder/export/$RESOURCES_ZIP"
        fi
        ;;
    export-small)
        # Create export directory in preset folder if it doesn't exist
        mkdir -p "$presetFolder/export"

        # First perform database dump
        echo "Exporting database..."
        MARIADB_USER=$(docker compose -p $projectName exec -T database env | grep MARIADB_USER | cut -d'=' -f2)
        MARIADB_PASSWORD=$(docker compose -p $projectName exec -T database env | grep MARIADB_PASSWORD | cut -d'=' -f2)
        MARIADB_DATABASE=$(docker compose -p $projectName exec -T database env | grep MARIADB_DATABASE | cut -d'=' -f2)

        # Create dump filename with timestamp
        DUMP_FILENAME="$(date +"%Y-%m-%d").sql"

        # Perform the mysqldump
        dump_command="mysqldump -u $MARIADB_USER -p$MARIADB_PASSWORD $MARIADB_DATABASE > /tmp/$DUMP_FILENAME"
        docker compose -p $projectName exec -T database bash -c "$dump_command"

        # Copy the SQL file back to the preset folder's export directory
        docker compose -p $projectName cp database:/tmp/$DUMP_FILENAME "$presetFolder/export/"

        # Export wb_resources with thumbnail filtering if it exists
        if [ -d "$presetFolder/wb_resources" ]; then
            echo "Exporting wb_resources with thumbnail filtering..."
            # Create zip file with timestamp
            RESOURCES_ZIP="wb_resources_small_$(date +"%Y-%m-%d").zip"

            # Remove existing zip file if it exists
            if [ -f "$presetFolder/export/$RESOURCES_ZIP" ]; then
                echo "Removing existing zip file..."
                rm -f "$presetFolder/export/$RESOURCES_ZIP"
            fi

            # Create temporary directory for filtered files
            TEMP_DIR=$(mktemp -d)
            mkdir -p "$TEMP_DIR/wb_resources"

            # Copy non-images directories as-is
            for dir in "$presetFolder/wb_resources"/*; do
                if [ -d "$dir" ] && [ "$(basename "$dir")" != "images" ]; then
                    cp -r "$dir" "$TEMP_DIR/wb_resources/"
                fi
            done

            # Copy images directory structure but filter thumb subdirectory
            if [ -d "$presetFolder/wb_resources/images" ]; then
                mkdir -p "$TEMP_DIR/wb_resources/images"

                # Copy non-thumb subdirectories as-is
                for subdir in "$presetFolder/wb_resources/images"/*; do
                    if [ -d "$subdir" ] && [ "$(basename "$subdir")" != "thumb" ]; then
                        cp -r "$subdir" "$TEMP_DIR/wb_resources/images/"
                    fi
                done

                # Process thumb directory with awk script to get smallest files
                if [ -d "$presetFolder/wb_resources/images/thumb" ]; then
                    echo "Filtering thumbnails to select smallest images from each directory..."
                    mkdir -p "$TEMP_DIR/wb_resources/images/thumb"

                    # Use find and ls to get file sizes, then apply awk script (more portable than stat)
                    find "$presetFolder/wb_resources/images/thumb" -type f -exec ls -la {} \; | \
                    awk '/^-/ {
                        gsub(/,/, "", $5);
                        size=$5+0;
                        path=$NF;
                        dir=path;
                        sub(/\/[^\/]*$/, "", dir);
                        if (!(dir in min) || size < min[dir]) {
                            min[dir] = size;
                            file[dir] = path
                        }
                    }
                    END {
                        for (d in file) print file[d]
                    }' | while read -r file_path; do
                        # Create directory structure and copy file
                        rel_path="${file_path#$presetFolder/wb_resources/images/thumb/}"
                        target_dir="$TEMP_DIR/wb_resources/images/thumb/$(dirname "$rel_path")"
                        mkdir -p "$target_dir"
                        cp "$file_path" "$target_dir/"
                    done
                fi
            fi

            # Create the zip file from filtered content
            # Get absolute path to avoid issues with relative paths
            EXPORT_DIR="$(realpath "$presetFolder/export")"
            ZIP_PATH="$EXPORT_DIR/$RESOURCES_ZIP"

            # Ensure export directory exists
            mkdir -p "$EXPORT_DIR"

            echo "Creating zip file at: $ZIP_PATH"
            if (cd "$TEMP_DIR" && zip -r "$ZIP_PATH" wb_resources/); then
                echo "wb_resources (with thumbnail filtering) exported to $presetFolder/export/$RESOURCES_ZIP"

                # Test the created zip file
                if ! unzip -t "$ZIP_PATH" >/dev/null 2>&1; then
                    echo "WARNING: Created zip file failed integrity test"
                    echo "Export may be incomplete or corrupted"
                fi
            else
                echo "ERROR: Failed to create wb_resources zip file with thumbnails"
                rm -rf "$TEMP_DIR"
                exit 1
            fi

            # Clean up temporary directory
            rm -rf "$TEMP_DIR"
        else
            echo "No wb_resources directory found in $presetFolder"
        fi

        echo "Export-small completed. Files saved to $presetFolder/export/"
        echo "Database dump: $presetFolder/export/$DUMP_FILENAME"
        if [ -d "$presetFolder/wb_resources" ]; then
            echo "Resources (thumbnails filtered): $presetFolder/export/$RESOURCES_ZIP"
        fi
        ;;
    import)
        # Check if export directory exists
        if [ ! -d "$presetFolder/export" ]; then
            echo "Export directory not found: $presetFolder/export"
            echo "Please run export first or ensure the export directory exists."
            exit 1
        fi

        # Find the most recent SQL dump file
        SQL_FILE=$(ls -t "$presetFolder/export"/*.sql 2>/dev/null | head -n1)
        if [ -z "$SQL_FILE" ]; then
            echo "No SQL dump file found in $presetFolder/export/"
            echo "Please ensure a .sql file exists in the export directory."
            exit 1
        fi

        echo "Found SQL dump: $SQL_FILE"

        # Import database dump
        echo "Importing database dump..."

        # Copy the SQL file into the container
        docker compose -p $projectName cp "$SQL_FILE" database:/tmp/import_dump.sql

        # Extract MySQL credentials and perform database import
        MARIADB_USER=$(docker compose -p $projectName exec -T database env | grep MARIADB_USER | cut -d'=' -f2)
        MARIADB_PASSWORD=$(docker compose -p $projectName exec -T database env | grep MARIADB_PASSWORD | cut -d'=' -f2)
        MARIADB_DATABASE=$(docker compose -p $projectName exec -T database env | grep MARIADB_DATABASE | cut -d'=' -f2)

        # Perform the import
        import_command="mysql -u $MARIADB_USER -p$MARIADB_PASSWORD $MARIADB_DATABASE < /tmp/import_dump.sql"
        docker compose -p $projectName exec -T database bash -c "$import_command"

        # Find and extract wb_resources zip file
        RESOURCES_ZIP=$(ls -t "$presetFolder/export"/wb_resources_*.zip 2>/dev/null | head -n1)
        #remove preset folder from resources zip
        RESOURCES_WO_FOLDER="export/$(basename $RESOURCES_ZIP)"
        if [ -n "$RESOURCES_ZIP" ]; then
            echo "Found wb_resources archive: $RESOURCES_ZIP"
            echo "Extracting wb_resources..."

            # Remove existing wb_resources directory if it exists and handle permission issues
            if [ -d "$presetFolder/wb_resources" ]; then
                echo "Removing existing wb_resources directory..."
                # First try with sudo to handle permission issues
                if ! sudo rm -rf "$presetFolder/wb_resources"; then
                    echo "Permission denied when removing wb_resources. Trying without sudo..."
                    if ! rm -rf "$presetFolder/wb_resources" 2>/dev/null; then
                        echo "ERROR: Cannot remove existing wb_resources directory due to permission issues."
                        echo "This usually happens when Docker creates files with different ownership."
                        echo "Please run one of the following commands manually:"
                        echo "  sudo rm -rf $presetFolder/wb_resources"
                        echo "  sudo chown -R \$(whoami):\$(whoami) $presetFolder/wb_resources && rm -rf $presetFolder/wb_resources"
                        echo "Then run the import command again."
                        exit 1
                    else
                        echo "Successfully removed wb_resources directory with sudo."
                    fi
                else
                    echo "Successfully removed wb_resources directory."
                fi
            fi

            # Test the zip file first
            echo "Testing zip file integrity..."
            if ! unzip -t "$RESOURCES_ZIP" >/dev/null 2>&1; then
                echo "ERROR: The zip file appears to be corrupted or invalid."
                echo "File: $RESOURCES_ZIP"
                echo "Try creating a new export or check the file manually."
                exit 1
            fi

            # Extract the zip file
            echo "Extracting wb_resources archive..."
            if (cd "$presetFolder" && unzip -o "$RESOURCES_WO_FOLDER"); then
                echo "wb_resources extracted successfully."
            else
                echo "ERROR: Failed to extract wb_resources archive."
                echo "File: $RESOURCES_ZIP"
                echo "The zip file tested OK but extraction failed. Check disk space and permissions."
                echo "You can try extracting manually with: cd $presetFolder && unzip -o $RESOURCES_WO_FOLDER"
                exit 1
            fi
        else
            echo "No wb_resources zip file found in export directory."
        fi

        echo "Import completed successfully."
        ;;
    fixpermissions)
        if [ ! -d "$presetFolder/wb_resources" ]; then
            echo "wb_resources directory not found: $presetFolder/wb_resources"
            exit 1
        fi

        # Check current ownership of the wb_resources directory
        current_user=$(stat -c '%U' "$presetFolder/wb_resources")
        current_group=$(stat -c '%G' "$presetFolder/wb_resources")

        echo "Current user: $current_user, Current group: $current_group"

        # Ask for confirmation to change permissions
        read -p "Do you want to change the ownership of wb_resources directory? (y/N): " confirm

        if [ "$confirm" == "y" ]; then
            echo "Changing ownership to the current user: $(whoami)"
            sudo chown -R "$(whoami):$(whoami)" "$presetFolder/wb_resources"
            echo "Successfully fixed permissions on $presetFolder/wb_resources. You can now modify or remove the directory normally."
        else
            echo "Permission change aborted."
        fi
        ;;
    mongodump)
        # Get the dump directory from parameter or use timestamp
        dump_dir="${3:-mongodb_$(date +"%Y-%m-%d")}"

        # Create export directory in preset folder if it doesn't exist
        mkdir -p "$presetFolder/export/$dump_dir"
        
        # Extract MongoDB credentials from environment
        MONGO_USERNAME=$(docker compose -p $projectName exec -T kompakkt-mongo env | grep MONGO_INITDB_ROOT_USERNAME | cut -d'=' -f2)
        MONGO_PASSWORD=$(docker compose -p $projectName exec -T kompakkt-mongo env | grep MONGO_INITDB_ROOT_PASSWORD | cut -d'=' -f2)

        # Create mongodump command
        dump_command="mongodump --uri=\"mongodb://${MONGO_USERNAME}:${MONGO_PASSWORD}@localhost:27017\" --out=/tmp/dump"

        # Execute mongodump
        echo "Creating MongoDB dump..."
        docker compose -p $projectName exec -T kompakkt-mongo bash -c "$dump_command"

        # Copy the dump directory back to the preset folder's export directory
        docker compose -p $projectName cp kompakkt-mongo:/tmp/dump/. "$presetFolder/export/$dump_dir/"

        echo "MongoDB dump completed and saved to $presetFolder/export/$dump_dir"
        ;;

    mongorestore)
        # Check if dump directory argument is provided
        dump_dir="${3:-}"
        if [ -z "$dump_dir" ]; then
            echo "Please provide the MongoDB dump directory as an argument."
            echo "Usage: $0 <preset_folder> mongorestore <dump_dir>"
            exit 1
        fi

        # Ensure the dump directory exists
        if [ ! -d "$dump_dir" ]; then
            echo "MongoDB dump directory not found. Please ensure the directory '$dump_dir' exists."
            exit 1
        fi

        # Extract MongoDB credentials from environment
        MONGO_USERNAME=$(docker compose -p $projectName exec -T kompakkt-mongo env | grep MONGO_INITDB_ROOT_USERNAME | cut -d'=' -f2)
        MONGO_PASSWORD=$(docker compose -p $projectName exec -T kompakkt-mongo env | grep MONGO_INITDB_ROOT_PASSWORD | cut -d'=' -f2)

        # Create temporary directory in container
        docker compose -p $projectName exec -T kompakkt-mongo mkdir -p /tmp/restore

        # Copy the dump directory into the container
        echo "Copying dump directory to MongoDB container..."
        docker compose -p $projectName cp "$dump_dir/." kompakkt-mongo:/tmp/restore/

        # Create mongorestore command
        restore_command="mongorestore --uri=\"mongodb://${MONGO_USERNAME}:${MONGO_PASSWORD}@localhost:27017\" --dir=/tmp/restore --drop"

        # Execute mongorestore
        echo "Restoring MongoDB dump..."
        docker compose -p $projectName exec -T kompakkt-mongo bash -c "$restore_command"

        echo "MongoDB restore completed."
        ;;

    resetPropertyCounter)
        # Commands to reset the property counter
        commands=(
            "echo 'SELECT * FROM /*_*/wb_id_counters;' | php maintenance/sql.php"
            "echo 'UPDATE /*_*/wb_id_counters SET id_value = 200 WHERE id_type = \"wikibase-property\";' | php maintenance/sql.php"
            "echo 'SELECT * FROM /*_*/wb_id_counters;' | php maintenance/sql.php"
        )

        for cmd in "${commands[@]}"; do
            command="docker compose -p $projectName exec -u 1000 wikibase bash -c \"$cmd\""
            echo "Executing following command: $command"
            eval $command
        done
        ;;
    init)
        # Check if template directory exists
        if [ ! -d "template" ]; then
            echo "Error: Template directory not found. Please ensure you're running this from the wikibase4research directory."
            exit 1
        fi

        # Check if config executable exists
        if [ ! -f "template/dist/w4r-config" ]; then
            echo "Error: w4r-config executable not found in template/dist directory."
            exit 1
        fi

        # Change to template directory
        echo "Changing to template directory..."
        cd template || exit 1

        # Run w4r-config
        echo "Running configuration script..."
        ./dist/w4r-config || {
            echo "Error: Configuration script failed."
            exit 1
        }

        echo "Configuration completed successfully!"
        ;;

    updatehash)
        # Fetch the latest hash from the extensions directory
        echo "Fetching latest Wikibase hash..."
        latest_hash=$(curl -s https://extdist.wmflabs.org/dist/extensions/ | grep "Wikibase-REL1_39-" | grep -v "Unlinked" | sed -n 's/.*Wikibase-REL1_39-\([^.]*\)\.tar\.gz.*/\1/p')

        if [ -z "$latest_hash" ]; then
            echo "Error: Could not fetch latest Wikibase hash"
            exit 1
        fi

        # Update the hash in extensionManagement.json
        config_file="$presetFolder/config/extensionManagement.json"
        if [ ! -f "$config_file" ]; then
            echo "Error: extensionManagement.json not found in $presetFolder/config/"
            exit 1
        fi
        echo "Latest Wikibase hash: $latest_hash"
        echo "The command will be:"
        echo "sed -i \"s/Wikibase-REL1_39-[a-f0-9]\{7\}/Wikibase-REL1_39-$latest_hash/\" \"$config_file\""
        sed -i "s/Wikibase-REL1_39-[a-f0-9]\{7\}/Wikibase-REL1_39-$latest_hash/" "$config_file"
        echo "Updated Wikibase hash to $latest_hash in $config_file"
        ;;
    *)
        command=$(build_compose_command "${W4R_COMPOSER_SERVICE_INCLUDE}")
        echo "Executing following command: $command --env-file $(get_env_file_from_preset "$presetFolder") $action ${@:3}"
        $command --env-file "$(get_env_file_from_preset "$presetFolder")" $action "${@:3}"
        ;;
esac

exit 0
