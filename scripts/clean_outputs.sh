#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

for folder in uploads outputs reports temp; do
  target="$ROOT_DIR/backend/storage/$folder"
  mkdir -p "$target"
  find "$target" -mindepth 1 ! -name ".gitkeep" -delete
  touch "$target/.gitkeep"
done

echo "Storage outputs cleaned."
