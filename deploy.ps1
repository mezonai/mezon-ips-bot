# Windows local build & deploy script in PowerShell
# Matches behavior of deploy.sh

$PSScriptRoot = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

$EnvFile = if ($env:ENV_FILE) { $env:ENV_FILE } else { ".env.prod" }

function Write-Log ($message) {
    Write-Host "[deploy] $message"
}

function Write-ErrorLog ($message) {
    Write-Host "[deploy] ERROR: $message" -ForegroundColor Red
}

# Require uv command
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-ErrorLog "Missing required command: uv. Please install uv first (e.g., using 'winget install astral-sh.uv' or 'powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`"')."
    exit 1
}

# Check files
if (Test-Path $EnvFile) {
    Write-Log "Loading environment variables from $EnvFile"
    # Export env vars from file, ignoring comments and empty lines
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#")) {
            if ($line -match "^([^=]+)=(.*)$") {
                $name = $Matches[1].Trim()
                $value = $Matches[2].Trim()
                # Remove quotes if present
                if (($value.StartsWith("'") -and $value.EndsWith("'")) -or ($value.StartsWith("`"") -and $value.EndsWith("`""))) {
                    $value = $value.Substring(1, $value.Length - 2)
                }
                [System.Environment]::SetEnvironmentVariable($name, $value, [System.EnvironmentVariableTarget]::Process)
            }
        }
    }
} else {
    # If .env.prod doesn't exist, try copying .env.prod.example
    if (Test-Path ".env.prod.example") {
        Write-Log "Copying .env.prod.example to .env.prod..."
        Copy-Item ".env.prod.example" ".env.prod"
        Write-Log "Created .env.prod. Please configure it and run deploy.ps1 again."
        exit 0
    } else {
        Write-ErrorLog "Env file not found: $EnvFile"
        exit 1
    }
}

Write-Log "Syncing dependencies with uv..."
uv sync --frozen --no-dev
if ($LASTEXITCODE -ne 0) {
    Write-ErrorLog "uv sync failed"
    exit 1
}

Write-Log "Running database migrations (Alembic)..."
uv run alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-ErrorLog "Alembic migrations failed"
    exit 1
}

Write-Log "Starting Mezon Bot natively..."
uv run python run.py --host 0.0.0.0 --port 8000

