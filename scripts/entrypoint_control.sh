#!/bin/sh

# Check if the marker file exists
if [ ! -f /marker_file ]; then
  # Download $W4R_DATA_MODEL_SCRIPT_URL
  wget -O /tmp/data_model.py $W4R_DATA_MODEL_SCRIPT_URL

  # Execute the command you want to run only on the first startup
  python /tmp/data_model.py

  # Execute additional commands
  python /app/custom_init.py
  # Your command here
  touch /marker_file
fi

# Continue with the default command
exec "$@"
