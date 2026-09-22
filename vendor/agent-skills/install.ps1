# Links every skill in skills/ into Claude Code's user-level skills
# directory (%USERPROFILE%\.claude\skills), so all projects on this machine
# pick them up without per-project setup. Uses directory junctions, which
# don't require admin rights on Windows. Safe to re-run; existing entries
# are skipped.

$repoSkillsDir = Join-Path $PSScriptRoot "skills"
$skillsDir = Join-Path $env:USERPROFILE ".claude\skills"

New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null

Get-ChildItem -Directory $repoSkillsDir | ForEach-Object {
    $target = Join-Path $skillsDir $_.Name
    if (Test-Path $target) {
        Write-Host "Skipping $($_.Name): already exists at $target"
        return
    }
    New-Item -ItemType Junction -Path $target -Target $_.FullName | Out-Null
    Write-Host "Linked $($_.Name) -> $target"
}

Write-Host "Done. Other tools (Codex, OpenCode, ...) have their own global skills directory:"
Write-Host "symlink skills/<name> into it the same way."
