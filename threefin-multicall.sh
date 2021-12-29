#!/usr/bin/env bash

# A small script to pass stdin to a Threefin module
# and print the reult to stdout. By default the module
# is chosen according to the base name of the file
# being executed, enabling the use of symbolic links
# or simply multiple copies to provide a selection
# of exposed modules.
# All further configuration happens via the THREEFIN_*
# environment variables, see below.
#
# Caveat administrator: At present this script ignores
# the system's proxy settings!

set -euo pipefail

thrf_module="${THREEFIN_MODULE:-"$(basename "$0" .sh)"}"

thrf_protocol="${THREEFIN_PROTOCOL:-https}"
thrf_host="${THREEFIN_HOST:-localhost}"
thrf_port="${THREEFIN_PORT:-12345}"
thrf_basepath="${THREEFIN_BASEPATH:-"/"}"

url_base_raw="${thrf_protocol}://${thrf_host}:${thrf_port}${thrf_basepath}"
url_base="${url_base_raw%/}"
url_tail="api/v0.1/module/${thrf_module}"

if test ! -t 0 ; then
    payload="$(cat)"
else
    echo "Must provide input on stdin" >&2 && exit 1
fi

curl --noproxy "${thrf_host}" "${url_base}/${url_tail}" -X POST --data "${payload}"
