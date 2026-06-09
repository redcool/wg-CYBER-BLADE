<#
.SYNOPSIS
    Extract version from cache-version.js and sync to index.html ?v= references

.DESCRIPTION
    Single source of truth: CACHE_VER in src/engine/cache-version.js
    Run this script after changing CACHE_VER to update all 39 ?v= references in index.html.

.USAGE
    powershell -File scripts/sync-version.ps1

.NOTES
    Requires PowerShell 5.1+
#>

$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$cacheFile = Join-Path (Join-Path $root "src") "engine\cache-version.js"
$htmlFile  = Join-Path $root "index.html"

# Extract version from cache-version.js
$match = Select-String -Path $cacheFile -Pattern "CACHE_VER\s*=\s*'(\d+)'"
if (-not $match) {
    Write-Error "Could not extract CACHE_VER from $cacheFile (expected: CACHE_VER = 'number')"
    exit 1
}

$version = $match.Matches.Groups[1].Value
Write-Host "Current version: v=$version"

# Read index.html and replace all ?v= references
$content = Get-Content -Path $htmlFile -Raw -Encoding UTF8
if (-not $content) {
    Write-Error "Could not read $htmlFile"
    exit 1
}

$newContent = $content -replace 'v=\d+', "v=$version"

if ($content -eq $newContent) {
    Write-Host "No ?v= references found or already up-to-date. No changes made."
} else {
    # Write with UTF-8 BOM to preserve encoding
    [System.IO.File]::WriteAllText($htmlFile, $newContent, [System.Text.UTF8Encoding]::new($true))
    Write-Host "Synced index.html all ?v= --> v=$version"
}
