#!/usr/bin/env bash
set -e

## Running __init__.py script
if [[ "${@: -1}" = "opentakserver.app" ]]; then
    python3 /etc/entrypoint.d/__init__.py --noinput
fi

## Running passed command
if [[ "$1" ]]; then
	exec "$@"
fi
