# Terminal playground for the Foundry Router Logic App.
# Usage:
#   $env:LOGIC_APP_URL = "<your trigger URL>"   # or put it in a local .env (see .env.example)
#   pwsh -File .\chat.ps1
# Type 'exit' or 'quit' to leave.
param([string]$Url = $env:LOGIC_APP_URL)

if (-not $Url) {
    $envFile = Join-Path $PSScriptRoot ".env"
    if (Test-Path $envFile) {
        foreach ($line in Get-Content $envFile) {
            if ($line -match '^\s*LOGIC_APP_URL\s*=\s*(.+)$') {
                $Url = $Matches[1].Trim().Trim('"')
            }
        }
    }
}

if (-not $Url) {
    Write-Host "No LOGIC_APP_URL found. Set the env var or create a .env file (see .env.example)." -ForegroundColor Yellow
    exit 1
}

Write-Host "Foundry Router playground - type 'exit' to quit." -ForegroundColor Cyan
Write-Host "Try: 'I was double charged on my last invoice'  or  'I can't log in'." -ForegroundColor DarkGray

while ($true) {
    $msg = Read-Host "you"
    if ($msg -in @('exit', 'quit')) { break }
    if ([string]::IsNullOrWhiteSpace($msg)) { continue }
    try {
        $body = @{ message = $msg } | ConvertTo-Json
        $resp = Invoke-WebRequest -Uri $Url -Method Post -ContentType "application/json" -Body $body -UseBasicParsing
        Write-Host "agent> $($resp.Content)`n" -ForegroundColor Green
    }
    catch {
        Write-Host "error> $($_.Exception.Message)`n" -ForegroundColor Red
    }
}
