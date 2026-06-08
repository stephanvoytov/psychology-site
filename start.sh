#!/usr/bin/env bash
set -o errexit

uv run gunicorn lyceum23.wsgi:application --bind 0.0.0.0:$PORT
