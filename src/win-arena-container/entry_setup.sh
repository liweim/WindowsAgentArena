#!/bin/bash

echo "Starting WinArena VM..."

# Start the VM script in the background
cd / # Fix for Azure ML Job not using the correct root path
bash /start_vm.sh &

# Wait for the VM to start up
while true; do
  # Send a GET request to the specified URL
  response=$(curl --write-out '%{http_code}' --silent --output /dev/null 20.20.20.21:5000/probe)

  # If the response code is 200 (HTTP OK), break the loop
  if [ $response -eq 200 ]; then
    break
  fi

  echo "Waiting for a response from the windows server. This might take a while..."

  # Wait for a while before the next attempt
  sleep 5
done

echo "VM is up and running, and the Windows Arena Server is ready to use!"

if [ -f /shared/on-logon.ps1 ]; then
  echo "Syncing dev WinArena server files into Windows C:\\oem..."
  python3 - <<'PY'
import requests
import time

command = r"""powershell -NoProfile -ExecutionPolicy Bypass -Command "New-Item -ItemType Directory -Path 'C:\oem\server' -Force | Out-Null; Copy-Item -Path '\\host.lan\Data\on-logon.ps1' -Destination 'C:\oem\on-logon.ps1' -Force; (Get-Content 'C:\oem\on-logon.ps1') -replace '^\$scriptFolder\s*=.*', '$scriptFolder = ''C:\oem''' | Set-Content 'C:\oem\on-logon.ps1'; Copy-Item -Path '\\host.lan\Data\server\*' -Destination 'C:\oem\server' -Recurse -Force"""
for attempt in range(1, 6):
    try:
        response = requests.post(
            "http://20.20.20.21:5000/execute",
            json={"shell": True, "command": command},
            timeout=(10, 120),
        )
        response.raise_for_status()
        break
    except (requests.ConnectionError, requests.Timeout) as exc:
        # Copying server source can trigger Flask's development reloader.
        # Repeating this file synchronization is safe after a lost response.
        if attempt == 5:
            raise SystemExit(f"Dev file sync failed after {attempt} attempts: {exc}")
        print(f"Windows server connection interrupted during dev file sync ({attempt}/5); retrying in 5 seconds.", flush=True)
        time.sleep(5)
payload = response.json()
if payload.get("status") != "success" or payload.get("returncode") != 0:
    raise SystemExit(f"Failed to sync dev files into C:\\oem: {payload}")
print("Synced dev WinArena server files into Windows C:\\oem.")
PY
fi
