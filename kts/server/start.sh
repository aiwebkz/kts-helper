#!/bin/sh
set -eu
cd "$(dirname "$0")"
docker compose config --quiet
mkdir -p data
chmod 700 data
docker compose up -d hbbs
# The official image has no shell; wait on the shared key files from the host.
attempt=0
until test -s data/id_ed25519 && test -s data/id_ed25519.pub; do
  attempt=$((attempt + 1))
  if test "$attempt" -ge 30; then
    docker compose logs --tail=30 hbbs
    echo "hbbs did not initialize its keys" >&2
    exit 1
  fi
  sleep 1
done
docker compose up -d hbbr
docker compose ps
printf '\nClient public key:\n'
cat data/id_ed25519.pub
printf '\n'
