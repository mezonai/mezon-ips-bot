# Windows packaging script for Mezon IPS Bot
# Run this to package the project into a timestamped zip for copying to the server

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ZipPath = "mezon-ips-bot-$Timestamp.zip"
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

Write-Host "Packaging Mezon IPS Bot into $ZipPath..."

# Create a temporary staging directory
$StageDir = "deploy_stage"
if (Test-Path $StageDir) {
    Remove-Item $StageDir -Recurse -Force
}
New-Item -ItemType Directory -Path $StageDir | Out-Null

# List of files and folders to copy
$ItemsToCopy = @(
    "app",
    "docs",
    "template",
    "alembic.ini",
    "pyproject.toml",
    "run.py",
    "uv.lock",
    ".env.example",
    ".env.prod.example",
    "deploy.sh",
    "deploy.ps1"
)

foreach ($item in $ItemsToCopy) {
    if (Test-Path $item) {
        Write-Host "Copying $item..."
        $dest = Join-Path $StageDir $item
        if (Test-Path $item -PathType Container) {
            Copy-Item -Path $item -Destination $dest -Recurse -Force
        } else {
            Copy-Item -Path $item -Destination $dest -Force
        }
    }
}

# Compress the staging directory
Write-Host "Compressing to $ZipPath..."
Compress-Archive -Path "$StageDir\*" -DestinationPath $ZipPath -Force

# Clean up staging directory
Remove-Item $StageDir -Recurse -Force

Write-Host "Done! $ZipPath has been created successfully." -ForegroundColor Green
Write-Host "Deployment steps on the server:"
Write-Host "1. Copy '$ZipPath' to your server."
Write-Host "2. Extract the zip file."
Write-Host "3. Run 'uv sync --frozen --no-dev' to install dependencies."
Write-Host "4. Copy '.env.prod.example' to '.env.prod' (or '.env') and configure credentials/paths."
Write-Host "5. Run 'uv run alembic upgrade head' to apply database migrations."
Write-Host "6. Run 'uv run python run.py --reload' or use the deploy script to start the bot."
