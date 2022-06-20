#!/usr/bin/env bash

# A small script to locally call multiple Threefin modules
# in sequence.
#
# Arguments:
#   1) Unix domain socket
#   2-X) Modules to call

set -euo pipefail

METHOD="POST"
BASE_URL="http://localhost/api/v0.1/module"


socket="$1"

for ((i=2;i<=$#;i+=1)); do 
    module_url="${BASE_URL}/${!i}"
    echo "Calling: ${module_url}" 1>&2
    curl --unix-socket "${socket}" -X "${METHOD}" "${module_url}" || true
done

