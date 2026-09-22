# Links every skill in vendor/agent-skills/skills/ into this project's
# Claude Code skills directory (.claude/skills/), so the project picks up
# the vendored skill library without a machine-wide install. Uses
# directory junctions, which don't require admin rights on Windows.
# Safe to re-run; existing entries are left alone.

$repoRoot = Split-Path -Parent $PSScriptRoot
$vendorSkillsDir = Join-Path $repoRoot "vendor\agent-skills\skills"
$targetSkillsDir = Join-Path $repoRoot ".claude\skills"

if (-not (Test-Path $vendorSkillsDir)) {
    Write-Error "Vendor skills dir not found at $vendorSkillsDir - did you run 'git submodule update --init'?"
    exit 1
}

New-Item -ItemType Directory -Force -Path $targetSkillsDir | Out-Null

Get-ChildItem -Directory $vendorSkillsDir | ForEach-Object {
    $target = Join-Path $targetSkillsDir $_.Name
    if (Test-Path $target) {
        Write-Host "Skipping $($_.Name): already exists at $target"
        return
    }
    New-Item -ItemType Junction -Path $target -Target $_.FullName | Out-Null
    Write-Host "Linked $($_.Name) -> $target"
}

Write-Host "Done."
