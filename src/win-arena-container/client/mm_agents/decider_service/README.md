# Decider service

The service loads `/home/weimingli/models/decider-2b` once and exposes the
official `system_one(state, questions)` interface over HTTP.

Start one persistent user service from any directory:

```bash
systemd-run --user --unit=decider-2b --collect \
  --property=Restart=on-failure --property=RestartSec=5 \
  --setenv=DECIDER_DEVICE=auto \
  /home/weimingli/miniconda3/envs/vllm/bin/python -m uvicorn \
  mm_agents.decider_service.server:app \
  --app-dir /home/weimingli/projects/WindowsAgentArena/src/win-arena-container/client \
  --host 0.0.0.0 --port 18766 --workers 1
```

Inspect or stop it with:

```bash
journalctl --user -u decider-2b -f
systemctl --user stop decider-2b
```

Health and request smoke tests:

```bash
curl http://127.0.0.1:18766/healthz
python -m mm_agents.decider_service.request
```

Environment variables:

- `DECIDER_MODEL`: local model directory.
- `DECIDER_DEVICE`: `auto`, `cpu`, `cuda`, or `cuda:<index>`.
- `DECIDER_MIN_CUDA_FREE_BYTES`: minimum free GPU memory used by `auto`;
  defaults to 5 GiB, otherwise the service loads on CPU.
- `DECIDER_URL`: endpoint used by LocalLSTC2; the container default is
  `http://host.docker.internal:18766/v1/systemone`.
- `DECIDER_TIMEOUT`: client request timeout in seconds; defaults to 300.

The service includes a local compatibility adapter for the Decider 1.9.0 CUDA
convolution patch and Transformers 5.8.0. It does not modify either installed
package and is reported as `conv_compat_patched` by `/healthz`.
