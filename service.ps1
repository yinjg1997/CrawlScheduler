param(
    [ValidateSet("start", "stop", "restart", "status")]
    [string]$Action = "start"
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$RunDir = Join-Path $RootDir "logs\run"

$Services = @(
    @{
        Name = "backend"
        WorkDir = $BackendDir
        PidFile = Join-Path $RunDir "backend.pid"
        OutLog = Join-Path $RunDir "backend.out.log"
        ErrLog = Join-Path $RunDir "backend.err.log"
    },
    @{
        Name = "frontend"
        WorkDir = $FrontendDir
        PidFile = Join-Path $RunDir "frontend.pid"
        OutLog = Join-Path $RunDir "frontend.out.log"
        ErrLog = Join-Path $RunDir "frontend.err.log"
    }
)

function Get-AliveProcess {
    param([string]$PidFile)

    if (-not (Test-Path $PidFile)) {
        return $null
    }

    $pidFileContent = (Get-Content $PidFile -Raw -ErrorAction SilentlyContinue).Trim()
    if (-not $pidFileContent) {
        return $null
    }

    $expectedStartTime = $null
    try {
        if ($pidFileContent.StartsWith("{")) {
            $pidInfo = $pidFileContent | ConvertFrom-Json
            $processId = [int]$pidInfo.pid
            $expectedStartTime = [datetime]$pidInfo.startTime
        } else {
            $processId = [int]$pidFileContent
        }

        $process = Get-Process -Id $processId -ErrorAction Stop
        if ($expectedStartTime -and ([datetime]$process.StartTime -ne $expectedStartTime)) {
            return $null
        }

        return $process
    } catch {
        return $null
    }
}

function Stop-ProcessTree {
    param([int]$ProcessId)

    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $ProcessId" -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        Stop-ProcessTree -ProcessId $child.ProcessId
    }

    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

function Resolve-PythonCommand {
    $candidates = @(
        @{
            File = Join-Path $BackendDir ".venv\Scripts\python.exe"
            Args = @("run.py")
        },
        @{
            File = Join-Path $RootDir ".venv\Scripts\python.exe"
            Args = @("run.py")
        }
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate.File) {
            return $candidate
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @{
            File = $python.Source
            Args = @("run.py")
        }
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return @{
            File = $py.Source
            Args = @("-3", "run.py")
        }
    }

    throw "Python executable not found. Install Python or create a virtual environment first."
}

function Start-App {
    param([hashtable]$Service)

    $alive = Get-AliveProcess -PidFile $Service.PidFile
    if ($alive) {
        Write-Output "$($Service.Name) is already running (PID $($alive.Id))."
        return
    }

    if ($Service.Name -eq "backend") {
        $command = Resolve-PythonCommand
    } else {
        $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
        if (-not $npm) {
            $npm = Get-Command npm -ErrorAction SilentlyContinue
        }
        if (-not $npm) {
            throw "npm executable not found. Install Node.js first."
        }
        $command = @{
            File = $npm.Source
            Args = @("run", "dev", "--", "--host", "0.0.0.0", "--port", "5173", "--strictPort")
        }
    }

    $process = Start-Process `
        -FilePath $command.File `
        -ArgumentList $command.Args `
        -WorkingDirectory $Service.WorkDir `
        -RedirectStandardOutput $Service.OutLog `
        -RedirectStandardError $Service.ErrLog `
        -PassThru `
        -WindowStyle Hidden

    @{
        name = $Service.Name
        pid = $process.Id
        startTime = ([datetime]$process.StartTime).ToString("o")
    } | ConvertTo-Json | Set-Content -Path $Service.PidFile
    Start-Sleep -Seconds 2

    $started = Get-AliveProcess -PidFile $Service.PidFile
    if ($started) {
        Write-Output "Started $($Service.Name) (PID $($process.Id))."
    } else {
        Remove-Item $Service.PidFile -ErrorAction SilentlyContinue
        Write-Output "Failed to start $($Service.Name). See $($Service.ErrLog)"
    }
}

function Stop-App {
    param([hashtable]$Service)

    $alive = Get-AliveProcess -PidFile $Service.PidFile
    if (-not $alive) {
        Remove-Item $Service.PidFile -ErrorAction SilentlyContinue
        Write-Output "$($Service.Name) is not running."
        return
    }

    Stop-ProcessTree -ProcessId $alive.Id
    Remove-Item $Service.PidFile -ErrorAction SilentlyContinue
    Write-Output "Stopped $($Service.Name) (PID $($alive.Id))."
}

function Show-Status {
    param([hashtable]$Service)

    $alive = Get-AliveProcess -PidFile $Service.PidFile
    if ($alive) {
        Write-Output "$($Service.Name): running (PID $($alive.Id))"
    } else {
        Write-Output "$($Service.Name): stopped"
    }
}

New-Item -ItemType Directory -Path $RunDir -Force | Out-Null

switch ($Action) {
    "start" {
        foreach ($service in $Services) {
            Start-App -Service $service
        }
        Write-Output ""
        Write-Output "Frontend: http://localhost:5173"
        Write-Output "Backend docs: http://localhost:8000/docs"
        Write-Output "Logs: $RunDir"
    }
    "stop" {
        $servicesToStop = @($Services)
        [array]::Reverse($servicesToStop)
        foreach ($service in $servicesToStop) {
            Stop-App -Service $service
        }
    }
    "restart" {
        $servicesToStop = @($Services)
        [array]::Reverse($servicesToStop)
        foreach ($service in $servicesToStop) {
            Stop-App -Service $service
        }
        foreach ($service in $Services) {
            Start-App -Service $service
        }
        Write-Output ""
        Write-Output "Frontend: http://localhost:5173"
        Write-Output "Backend docs: http://localhost:8000/docs"
        Write-Output "Logs: $RunDir"
    }
    "status" {
        foreach ($service in $Services) {
            Show-Status -Service $service
        }
    }
}
