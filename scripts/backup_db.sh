#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB_PATH="${REPO_ROOT}/db.sqlite3"
BACKUP_DIR="${REPO_ROOT}/backups"
RETENTION_DAYS=14

mkdir -p "$BACKUP_DIR"

if [[ ! -f "$DB_PATH" ]]; then
  echo "❌ DB not found at: $DB_PATH"
  exit 1
fi

if ! command -v sqlite3 >/dev/null 2>&1; then
  echo "❌ sqlite3 not found. Install it first (macOS: brew install sqlite)."
  exit 1
fi

TS="$(date +%d-%m-%y_%H-%M-%S)"
OUT="${BACKUP_DIR}/db_${TS}.sqlite3"

echo "▶ Backing up $DB_PATH -> $OUT.gz"
sqlite3 "$DB_PATH" ".backup '${OUT}'"
gzip -f "$OUT"

find "$BACKUP_DIR" -name "db_*.sqlite3.gz" -mtime +"$RETENTION_DAYS" -delete
echo "✅ Done."
