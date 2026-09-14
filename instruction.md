# Server side
## Add your tasks to this folder, following the same structure used in OSWorld

```text
/home/weimingli/projects/WindowsAgentArena/src/win-arena-container/client/evaluation_examples_windows/examples/accessibility/
```

## Run a task to verify it manually

```bash
conda activate winarena
cd /home/weimingli/projects/WindowsAgentArena/scripts
python run_human.py --example ../src/win-arena-container/client/evaluation_examples_windows/examples/cognitive/access-chrome_immersive_reader_extension.json
```

## Run tasks with an agent framework

The entry scripts for different agent frameworks are located at:

```text
scripts/run_*.sh
```

For example, run the LocalLSTC framework with:

```bash
bash scripts/run_locallstc.sh
```

Its log is written to:

```text
nohup_locallstc.out
```

To monitor task results in real time, run:

```bash
watch -n 1 python -m src.win-arena-container.client.mm_agents.utils
```

# Client side
## Connect remotely using Windows App

### Config ssh in your vscode-config
```text
Host CSE_LOGIN
  HostName login.cse.unsw.edu.au
  User your-zID
  ForwardX11 Yes

Host CSE_T2
  HostName 129.94.175.253
  User your-name
  ProxyJump CSE_LOGIN
  LocalForward 3390 127.0.0.1:3390
```

### Open the SSH tunnel

```bash
ssh -N -L 3390:localhost:3390 CSE_T2
```

### Open **Windows App** and enter the following address to connect

```text
localhost:3390
```

### Login credentials

```text
Username: .\Docker
Password: (leave blank)
```

## Connect to Self-hosted services
Add `LocalForward <port> 127.0.0.1:<port>` under your CSE_T2 SSH config, then connecting with ssh CSE_T2 and opening http://localhost:<port>/ in your browser while keeping the SSH session open.
