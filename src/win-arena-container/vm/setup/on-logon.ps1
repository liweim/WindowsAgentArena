$pythonScriptFile = "C:\Users\Docker\AppData\Local\Programs\Python\Python310\python.exe"
$pythonServerPort = 5000

# Start the Caddy reverse proxy in a non-blocking manner
Write-Host "Running the Caddy reverse proxy from port 9222 to port 1337"
Start-Process -NoNewWindow -FilePath "powershell" -ArgumentList "-Command", "caddy reverse-proxy --from :9222 --to :1337"

# Start the WinArena server
Write-Host "Running the WinArena server on port $pythonServerPort..."
python $pythonScriptFile --port $pythonServerPort
