$scriptFolder = "\\host.lan\Data"
$pythonScriptFile = "$scriptFolder\server\main.py"
$pythonServerPort = 5000

# Start the Caddy reverse proxy in a non-blocking manner
Write-Host "Running the Caddy reverse proxy from port 9222 to port 1337"
Start-Process -NoNewWindow -FilePath "powershell" -ArgumentList "-Command", "caddy reverse-proxy --from :9222 --to :1337"

# Start the WinArena server with the CPython installed by setup.ps1. LibreOffice
# also provides a python.exe, but it does not contain the Arena dependencies.
# Keep it detached so /setup/close_all cannot terminate it with this PowerShell.
$pythonExecutable = "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe"
Write-Host "Running the WinArena server on port $pythonServerPort..."
Start-Process `
    -WindowStyle Hidden `
    -FilePath $pythonExecutable `
    -ArgumentList "`"$pythonScriptFile`" --port $pythonServerPort"
