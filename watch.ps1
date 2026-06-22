# watch.ps1 - Automatically regenerates preview on save
$workspaceDir = $PSScriptRoot
$scriptPath = Join-Path $workspaceDir "generate_preview.py"

Write-Host "Watching for changes in .tex files..." -ForegroundColor Cyan

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $workspaceDir
$watcher.Filter = "*.tex"
$watcher.IncludeSubdirectories = $false
$watcher.EnableRaisingEvents = $true

$action = {
    $path = $Event.SourceEventArgs.FullPath
    $changeType = $Event.SourceEventArgs.ChangeType
    Write-Host "`n[$((Get-Date).ToString('HH:mm:ss'))] Detected $changeType on $(Split-Path $path -Leaf). Recompiling..." -ForegroundColor Yellow
    
    # Run the Python compilation script
    & C:\Users\veera\AppData\Local\Python\bin\python.exe $scriptPath
    
    Write-Host "`nWaiting for changes..." -ForegroundColor Cyan
}

# Register events for file modifications and creations
Register-ObjectEvent $watcher "Changed" -Action $action | Out-Null
Register-ObjectEvent $watcher "Created" -Action $action | Out-Null

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    # Clean up the watcher if the script is stopped
    Get-EventSubscriber | Unregister-Event
    $watcher.Dispose()
}
