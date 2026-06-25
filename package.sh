#!/usr/bin/env bash
# Bash packaging script for Mezon IPS Bot
# Run this to package the project into mezon-ips-bot.tar.gz for copying to the server

set -euo pipefail

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TAR_PATH="mezon-ips-bot-$TIMESTAMP.tar.gz"
ZIP_PATH="mezon-ips-bot-$TIMESTAMP.zip"

rm -f "$TAR_PATH" "$ZIP_PATH"

echo "Packaging Mezon IPS Bot into $TAR_PATH..."

# Stage files
STAGE_DIR="deploy_stage"
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"

ITEMS=(
  "app"
  "docs"
  "template"
  "alembic.ini"
  "pyproject.toml"
  "run.py"
  "uv.lock"
  ".env.example"
  ".env.prod.example"
  "deploy.sh"
  "deploy.ps1"
)

for item in "${ITEMS[@]}"; do
  if [ -e "$item" ]; then
    echo "Copying $item..."
    cp -R "$item" "$STAGE_DIR/"
  fi
done

# Compress
cd "$STAGE_DIR"
tar -czf "../$TAR_PATH" *
if command -v zip >/dev/null 2>&1; then
  zip -r "../$ZIP_PATH" * >/dev/null
fi
cd ..

rm -rf "$STAGE_DIR"

echo "Done! mezon-ips-bot.tar.gz (and mezon-ips-bot.zip) created successfully."
echo "Deployment steps on the server:"
echo "1. Copy the archive to the server."
echo "2. Extract it: tar -xzf mezon-ips-bot.tar.gz"
echo "3. Run 'uv sync --frozen --no-dev' to install dependencies."
echo "4. Copy '.env.prod.example' to '.env.prod' (or '.env') and configure credentials/paths."
echo "5. Run 'uv run alembic upgrade head' to apply database migrations."
echo "6. Run 'uv run python run.py --reload' or use the deploy script to start the bot."
