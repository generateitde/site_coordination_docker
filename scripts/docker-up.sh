#!/usr/bin/env bash
set -euo pipefail

HOST_IP=${HOST_IP:-$(hostname -I | awk '{print $1}')}
export HOST_IP

echo "Using HOST_IP=${HOST_IP}"
docker compose up --build "$@"
