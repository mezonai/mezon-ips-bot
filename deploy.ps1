# Windows local build & deploy script in PowerShell
# Matches behavior of deploy.sh

$PSScriptRoot = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

$ComposeFile = if ($env:COMPOSE_FILE) { $env:COMPOSE_FILE } else { "docker-compose.prod.yml" }
$EnvFile = if ($env:ENV_FILE) { $env:ENV_FILE } else { ".env.prod" }
$WaitTimeoutSeconds = if ($env:WAIT_TIMEOUT_SECONDS) { [int]$env:WAIT_TIMEOUT_SECONDS } else { 120 }
$PollIntervalSeconds = 5

function Write-Log ($message) {
    Write-Host "[deploy] $message"
}

function Write-ErrorLog ($message) {
    Write-Host "[deploy] ERROR: $message" -ForegroundColor Red
}

# Require docker command
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-ErrorLog "Missing required command: docker"
    exit 1
}

# Check docker compose version (V2)
docker compose version > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-ErrorLog "Docker Compose v2 is required"
    exit 1
}

# Check files
if (!(Test-Path $ComposeFile)) {
    Write-ErrorLog "Compose file not found: $ComposeFile"
    exit 1
}
if (!(Test-Path $EnvFile)) {
    Write-ErrorLog "Env file not found: $EnvFile. Copy .env.prod.example to .env.prod and fill in real values."
    exit 1
}

# Helper to run docker compose
function Invoke-DockerCompose {
    param(
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$Arguments
    )
    docker compose --env-file $EnvFile -f $ComposeFile @Arguments
}

Write-Log "Validating compose configuration"
Invoke-DockerCompose config > $null
if ($LASTEXITCODE -ne 0) {
    Write-ErrorLog "Compose configuration validation failed"
    exit 1
}

Write-Log "Building application image from local source"
Invoke-DockerCompose build app
if ($LASTEXITCODE -ne 0) {
    Write-ErrorLog "Building application image failed"
    exit 1
}

Write-Log "Starting services"
Invoke-DockerCompose up -d --remove-orphans
if ($LASTEXITCODE -ne 0) {
    Write-ErrorLog "Starting services failed"
    exit 1
}

function Wait-ForAppHealth {
    $containerId = (Invoke-DockerCompose ps -q app 2>$null)
    if ([string]::IsNullOrWhiteSpace($containerId)) {
        Write-ErrorLog "App container was not created"
        return $false
    }
    $containerId = $containerId.Trim()

    $deadline = (Get-Date).AddSeconds($WaitTimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $status = (docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' $containerId 2>$null)
        if ($null -ne $status) {
            $status = $status.Trim()
        } else {
            $status = ""
        }
        
        switch ($status) {
            "healthy" {
                Write-Log "App container is healthy"
                return $true
            }
            "running" {
                Write-Log "Waiting for app health: $status"
            }
            "starting" {
                Write-Log "Waiting for app health: $status"
            }
            default {
                Invoke-DockerCompose logs --tail=100 app
                Write-ErrorLog "App container is not healthy (status: $status)"
                return $false
            }
        }
        Start-Sleep -Seconds $PollIntervalSeconds
    }

    Invoke-DockerCompose logs --tail=100 app
    Write-ErrorLog "Timed out after $($WaitTimeoutSeconds)s waiting for app health"
    return $false
}

$healthSuccess = Wait-ForAppHealth
if (-not $healthSuccess) {
    exit 1
}

Write-Log "Current service status"
Invoke-DockerCompose ps
