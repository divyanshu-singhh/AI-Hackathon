#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../backend"
python -m venv .venv

if [ -f ".venv/Scripts/activate" ]; then
  # Windows Git Bash
  source .venv/Scripts/activate
else
  source .venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt
mkdir -p storage/uploads storage/outputs storage/reports storage/temp
touch storage/uploads/.gitkeep storage/outputs/.gitkeep storage/reports/.gitkeep storage/temp/.gitkeep

echo "Backend setup complete. Copy ../.env.example to .env and set IM_LLM_API_KEY."
