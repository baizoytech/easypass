$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root

function Get-PythonCommand {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @{ Exe = $python.Source; Args = @() }
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return @{ Exe = $py.Source; Args = @('-3') }
    }

    throw 'Python was not found. Please install Python 3.9+ and ensure it is available in PATH.'
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Exe,

        [Parameter(Mandatory = $true)]
        [string[]]$Args,

        [Parameter(Mandatory = $true)]
        [string]$ActionName,

        [Parameter(Mandatory = $true)]
        [string]$FailureHint
    )

    & $Exe @Args
    if ($LASTEXITCODE -ne 0) {
        throw "$ActionName failed with exit code $LASTEXITCODE. $FailureHint"
    }
}

$pythonCmd = Get-PythonCommand

$templates = Join-Path $root 'src\templates'
$static = Join-Path $root 'src\static'
$distDir = Join-Path $root 'dist'
$buildDir = Join-Path $root 'build'
$outputExe = Join-Path $distDir 'EasyPass.exe'

New-Item -ItemType Directory -Force -Path $distDir, $buildDir | Out-Null

$pyinstallerCheckArgs = @($pythonCmd.Args + @('-m', 'PyInstaller', '--version'))
Invoke-CheckedCommand `
    -Exe $pythonCmd.Exe `
    -Args $pyinstallerCheckArgs `
    -ActionName 'PyInstaller preflight check' `
    -FailureHint 'Install it with: python -m pip install pyinstaller'

$pyinstallerArgs = @(
    '-m', 'PyInstaller',
    '--noconfirm',
    '--clean',
    '--onefile',
    '--name', 'EasyPass',
    '--distpath', $distDir,
    '--workpath', $buildDir,
    '--specpath', $buildDir,
    '--add-data', "$templates;src/templates",
    '--add-data', "$static;src/static",
    (Join-Path $root 'src\desktop.py')
)

Write-Host "Building EasyPass.exe..."
Invoke-CheckedCommand `
    -Exe $pythonCmd.Exe `
    -Args @($pythonCmd.Args + $pyinstallerArgs) `
    -ActionName 'EasyPass packaging' `
    -FailureHint 'See the output above for the build error.'

Write-Host ""
if (-not (Test-Path $outputExe)) {
    throw "Build completed but the output file was not found: $outputExe"
}

Write-Host "Build finished:"
Write-Host ("  " + $outputExe)
