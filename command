1. Start the container:

```bash
cd /home/weimingli/projects/WindowsAgentArena/scripts
./run-local.sh --start-client false
```

2. Run `human_run.py`:

```bash
./run-local.sh --connect true
cd /client
python human_run.py
```

3. Connect remotely using Windows App:

3.1 First, open the SSH tunnel:

```bash
ssh -N -L 9006:localhost:9006 -L 3390:localhost:3390 CSE_T2
```

3.2 Open **Windows App** on your Mac.

3.3 Enter the following address to connect:

```text
localhost:13390
```

3.4 Login credentials:

```text
Username: .\Docker
Password: (leave blank)
```
