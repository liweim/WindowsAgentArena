# Parakeet ASR service

The service loads the local `parakeet-tdt-0.6b-v2.nemo` checkpoint once and
exposes a multipart HTTP transcription endpoint.

Start one persistent user service from any directory. The command calls the
environment's Python directly and does not require Conda activation:

```bash
systemd-run --user --unit=parakeet-asr --collect \
  --property=Restart=on-failure --property=RestartSec=5 \
  --setenv=PARAKEET_DEVICE=auto \
  /home/weimingli/miniconda3/envs/vllm/bin/python -m uvicorn \
  mm_agents.parakeet_asr.server:app \
  --app-dir /home/weimingli/projects/WindowsAgentArena/src/win-arena-container/client \
  --host 0.0.0.0 --port 18765 --workers 1
```

Inspect logs with `journalctl --user -u parakeet-asr -f` and stop it with
`systemctl --user stop parakeet-asr`.

Run the included request against the default test MP3:

```bash
python -m mm_agents.parakeet_asr.request
```

Request word timestamps when needed:

```bash
python -m mm_agents.parakeet_asr.request --timestamps
```

Environment variables:

- `PARAKEET_MODEL`: path to the `.nemo` checkpoint.
- `PARAKEET_DEVICE`: `auto`, `cuda`, or `cpu`.
- `PARAKEET_MAX_UPLOAD_BYTES`: maximum request file size; defaults to 500 MiB.
