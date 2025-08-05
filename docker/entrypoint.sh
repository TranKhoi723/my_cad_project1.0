#!/bin/bash

# This line ensures the script will exit immediately if any command fails
set -e

# "exec" will replace the process of this script with the command passed to it.
# "$@" is a special variable in bash, representing ALL parameters
# passed to the script (e.g., "freecadcmd", "/app/scripts/pipeline.py").
exec "$@"
