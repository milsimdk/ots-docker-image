#!/usr/bin/env bash
set -e

## Running __init__.py script
if [[ "${@: -1}" = "/app/.opentakserver_venv/bin/opentakserver" ]]; then
    python3 /etc/entrypoint.d/__init__.py --noinput
fi

## Running passed command
if [[ "$1" ]]; then
	exec "$@"
fi
