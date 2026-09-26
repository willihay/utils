$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = (Get-Location).Path
$propertiesPath = Join-Path $projectRoot "gradle.properties"

if (-not (Test-Path -LiteralPath $propertiesPath)) {
    throw "gradle.properties was not found in the current directory. Run this script from the project root."
}

$minecraftVersion = $null
foreach ($line in Get-Content -LiteralPath $propertiesPath) {
    if ($line -match '^\s*minecraft_version\s*=\s*(.+?)\s*$') {
        $minecraftVersion = $Matches[1].Trim()
        break
    }
}

if ([string]::IsNullOrWhiteSpace($minecraftVersion)) {
    throw "minecraft_version was not found in gradle.properties."
}

$gradlew = Join-Path $projectRoot "gradlew.bat"
if (-not (Test-Path -LiteralPath $gradlew)) {
    throw "gradlew.bat was not found in the current directory. Run this script from the project root."
}

Write-Host "Generating Minecraft sources for $minecraftVersion..."
& $gradlew genSources
if ($LASTEXITCODE -ne 0) {
    throw "genSources failed with exit code $LASTEXITCODE."
}

$minecraftMavenRoot = Join-Path $projectRoot ".gradle\loom-cache\minecraftMaven\net\minecraft"
if (-not (Test-Path -LiteralPath $minecraftMavenRoot)) {
    throw "Loom Minecraft cache was not found at $minecraftMavenRoot."
}

$sourceJars = Get-ChildItem -LiteralPath $minecraftMavenRoot -Recurse -File -Filter "*$minecraftVersion*-sources.jar" |
    Where-Object { $_.Name -match '^minecraft-.+-sources\.jar$' } |
    Sort-Object FullName

if ($sourceJars.Count -eq 0) {
    throw "No Minecraft source jars for $minecraftVersion were found under $minecraftMavenRoot."
}

$destinationRoot = Join-Path "C:\minecraft-assets" $minecraftVersion
$sourceDestination = Join-Path $destinationRoot "source"
New-Item -ItemType Directory -Force -Path $sourceDestination | Out-Null

Write-Host "Extracting Minecraft sources into $sourceDestination..."
foreach ($sourceJar in $sourceJars) {
    Write-Host "Extracting $($sourceJar.Name)"
    Push-Location $sourceDestination
    try {
        & jar xf $sourceJar.FullName
        if ($LASTEXITCODE -ne 0) {
            throw "jar failed with exit code $LASTEXITCODE while extracting $($sourceJar.FullName)."
        }
    }
    finally {
        Pop-Location
    }
}

Write-Host "Done. Extracted $($sourceJars.Count) Minecraft source jar(s) to $sourceDestination."
