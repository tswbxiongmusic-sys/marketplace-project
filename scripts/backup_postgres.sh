#!/usr/bin/env bash
# Run from the project root: bash scripts/backup_postgres.sh
# Keep the produced .dump file in encrypted object storage or another secure location.
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$project_dir/.env"
backup_dir="$project_dir/backups"

if [ ! -f "$env_file" ]; then
  echo "Missing .env file. Backup was not created." >&2
  exit 1
fi

set -a
. "$env_file"
set +a

timestamp="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$backup_dir"
export PGPASSWORD="$DATABASE_PASSWORD"
pg_dump --format=custom --no-owner --no-acl \
  --host="$DATABASE_HOST" --port="$DATABASE_PORT" --username="$DATABASE_USER" \
  --file="$backup_dir/marketplace-$timestamp.dump" "$DATABASE_NAME"
unset PGPASSWORD
echo "Backup created: $backup_dir/marketplace-$timestamp.dump"
