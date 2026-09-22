# Renders a diagram source file to an image, picking the renderer by input
# extension: .mmd -> Mermaid CLI, .puml -> PlantUML jar, .dot/.gv -> Graphviz.
# Output format is inferred from -OutputFile's extension (svg/png/pdf).
#
# Usage: render.ps1 -InputFile diagram.mmd -OutputFile diagram.svg

param(
    [Parameter(Mandatory = $true)][string]$InputFile,
    [Parameter(Mandatory = $true)][string]$OutputFile
)

$ErrorActionPreference = "Stop"

function Find-Dot {
    $cmd = Get-Command dot.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $found = Get-ChildItem "$env:ProgramFiles\Graphviz*\bin\dot.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { return $found.FullName }
    throw "Graphviz's dot.exe not found on PATH or under Program Files. Install it (winget install -e --id Graphviz.Graphviz) or add it to PATH."
}

function Find-Chrome {
    if ($env:LOCAL_DIAGRAMS_CHROME_PATH -and (Test-Path $env:LOCAL_DIAGRAMS_CHROME_PATH)) {
        return $env:LOCAL_DIAGRAMS_CHROME_PATH
    }
    $candidates = @(
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }
    throw "No Chrome/Edge found. Set LOCAL_DIAGRAMS_CHROME_PATH to a Chromium-based browser's executable."
}

$inExt = [System.IO.Path]::GetExtension($InputFile).ToLowerInvariant()
$outExt = [System.IO.Path]::GetExtension($OutputFile).TrimStart(".").ToLowerInvariant()

switch ($inExt) {
    ".mmd" {
        $chrome = Find-Chrome
        $configPath = Join-Path $env:TEMP "local-diagrams-puppeteer-config.json"
        @{ executablePath = $chrome } | ConvertTo-Json | Set-Content -Path $configPath
        mmdc -i $InputFile -o $OutputFile -p $configPath
    }
    ".puml" {
        $jar = $env:PLANTUML_JAR
        if (-not $jar) { $jar = Join-Path $env:LOCALAPPDATA "plantuml\plantuml.jar" }
        if (-not (Test-Path $jar)) { throw "PlantUML jar not found at $jar. Set PLANTUML_JAR or download from https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar" }
        $outDir = Split-Path -Parent $OutputFile
        if (-not $outDir) { $outDir = "." }
        New-Item -ItemType Directory -Force -Path $outDir | Out-Null
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($InputFile)
        java -jar $jar "-t$outExt" -o $outDir $InputFile
        $generated = Join-Path $outDir "$baseName.$outExt"
        $wantedLeaf = [System.IO.Path]::GetFileName($OutputFile)
        if ($wantedLeaf -ne "$baseName.$outExt") {
            Move-Item -Force $generated $OutputFile
        }
    }
    { $_ -in ".dot", ".gv" } {
        $dot = Find-Dot
        & $dot "-T$outExt" $InputFile -o $OutputFile
    }
    default {
        throw "Unknown diagram extension '$inExt'. Expected .mmd, .puml, .dot, or .gv."
    }
}

Write-Host "Rendered $InputFile -> $OutputFile"
