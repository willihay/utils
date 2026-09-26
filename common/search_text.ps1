param(
    [Parameter(Mandatory=$true)]
    [string]$Pattern,

    [switch]$Recurse,

    [switch]$IgnoreCase
)

# Determine search options
$searchOptions = @{}
if ($IgnoreCase) {
    $searchOptions["CaseSensitive"] = $false
} else {
    $searchOptions["CaseSensitive"] = $true
}

# Helper: check if file contains non-printable characters
function Test-Printable {
    param([byte[]]$Bytes)
    foreach ($b in $Bytes) {
        if ($b -lt 32 -and $b -notin @(9,10,13)) {
            return $false
        }
    }
    return $true
}

# Get files
$files = Get-ChildItem -File -ErrorAction SilentlyContinue -Recurse:$Recurse

foreach ($file in $files) {

    $ext = $file.Extension.ToLower()

    # If compressed, use 7z to stream content
    if ($ext -in @(".zip", ".gz", ".7z", ".xz", ".bz2", ".tar")) {

        try {
            $content = 7z e -so $file.FullName 2>$null
            if (-not $content) { continue }

            # Convert to bytes to check printability
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
            if (-not (Test-Printable $bytes)) { continue }

            if ($IgnoreCase) {
                if ($content -match $Pattern) {
                    Write-Host "MATCH (compressed): $($file.FullName)"
                }
            } else {
                if ($content -cmatch $Pattern) {
                    Write-Host "MATCH (compressed): $($file.FullName)"
                }
            }
        }
        catch {
            Write-Host "Failed to read compressed file: $($file.FullName)"
        }

        continue
    }

    # Normal file
    try {
        $bytes = [System.IO.File]::ReadAllBytes($file.FullName)
        if (-not (Test-Printable $bytes)) { continue }

        $text = [System.Text.Encoding]::UTF8.GetString($bytes)

        if ($IgnoreCase) {
            if ($text -match $Pattern) {
                Write-Host "MATCH: $($file.FullName)"
            }
        } else {
            if ($text -cmatch $Pattern) {
                Write-Host "MATCH: $($file.FullName)"
            }
        }
    }
    catch {
        Write-Host "Failed to read file: $($file.FullName)"
    }
}
