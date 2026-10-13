# Decider service

The service loads `/home/weimingli/models/decider-2b` once and exposes the
official `system_one(state, questions)` interface over HTTP.

Start one persistent user service from any directory:

```bash
systemd-run --user --unit=decider-2b --collect \
  --property=Restart=on-failure --property=RestartSec=5 \
  --setenv=DECIDER_DEVICE=auto \
  --setenv=DECIDER_CUDA_MEMORY_FRACTION=0.25 \
  --setenv=DECIDER_USE_GRAPHS=false \
  --setenv=DECIDER_SHARED_FORK_GB=1 \
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
- `DECIDER_CUDA_MEMORY_FRACTION`: optional hard limit for the process's PyTorch
  CUDA allocator, expressed as a fraction in `(0, 1]`. For example, `0.25`
  limits the process to roughly 20 GiB on an 80 GiB GPU. Requests exceeding
  the limit fail with CUDA OOM; they are not automatically moved to CPU.
- `DECIDER_USE_GRAPHS`: whether Decider uses retained CUDA graphs. Defaults to
  `true`; setting it to `false` substantially reduces persistent GPU memory at
  the cost of inference speed.
- `DECIDER_SHARED_FORK_GB`: temporary GPU-memory budget used by Decider when
  forking a shared state prefix. Decider defaults to 8 GiB; `1` is a
  conservative setting for a memory-constrained deployment.
- `DECIDER_URL`: endpoint used by LocalLSTC2; the container default is
  `http://129.94.173.199:18766/v1/systemone`. Override it when the service is
  deployed at a different address.
- `DECIDER_TIMEOUT`: client request timeout in seconds; defaults to 300.

The service includes a local compatibility adapter for the Decider 1.9.0 CUDA
convolution patch and Transformers 5.8.0. It does not modify either installed
package and is reported as `conv_compat_patched` by `/healthz`.
