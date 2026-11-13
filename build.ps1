# PowerShell Build Script for Virtual ECU
$ErrorActionPreference = "Stop"

if (-not (Get-Command gcc -ErrorAction SilentlyContinue)) {
    if (Test-Path "C:\msys64\ucrt64\bin") {
        $env:PATH = "C:\msys64\ucrt64\bin;$env:PATH"
    } elseif (Test-Path "C:\msys64\mingw64\bin") {
        $env:PATH = "C:\msys64\mingw64\bin;$env:PATH"
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$buildDir = "firmware/build"
if (-not (Test-Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir | Out-Null
}

Write-Host ">>> Compiling Virtual ECU Shared Library (DLL)..." -ForegroundColor Cyan
gcc -std=c11 -Wall -Wextra -O2 -DBUILDING_ECU_DLL -shared -I firmware/include `
    firmware/src/ecu_diagnostics.c `
    firmware/src/ecu_sensors.c `
    firmware/src/ecu_actuators.c `
    firmware/src/ecu_state_machine.c `
    firmware/src/ecu_fault_injection.c `
    firmware/src/ecu_firmware.c `
    -o "$buildDir/virtual_ecu.dll"

Write-Host ">>> Compiling Virtual ECU Standalone CLI (EXE)..." -ForegroundColor Cyan
gcc -std=c11 -Wall -Wextra -O2 -I firmware/include `
    firmware/src/ecu_diagnostics.c `
    firmware/src/ecu_sensors.c `
    firmware/src/ecu_actuators.c `
    firmware/src/ecu_state_machine.c `
    firmware/src/ecu_fault_injection.c `
    firmware/src/ecu_firmware.c `
    firmware/src/main.c `
    -o "$buildDir/virtual_ecu.exe"

Write-Host ">>> Build completed successfully!" -ForegroundColor Green
Write-Host "    Artifacts: $buildDir/virtual_ecu.dll, $buildDir/virtual_ecu.exe"

