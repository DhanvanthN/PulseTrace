# Example backup — set $Password locally; do not commit secrets.
param(
    [string]$HostName = "localhost",
    [int]$Port = 5433,
    [string]$User = "pulsetrace",
    [string]$Database = "pulsetrace",
    [string]$OutFile = "pulsetrace_backup.dump"
)

if (-not $env:PGPASSWORD) {
    Write-Error "Set PGPASSWORD in the environment before running this script."
    exit 1
}

pg_dump -h $HostName -p $Port -U $User -d $Database -Fc -f $OutFile
Write-Host "Wrote $OutFile"