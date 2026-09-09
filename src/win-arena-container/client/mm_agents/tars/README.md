# TARS for WindowsAgentArena

This package ports LocalGUI's TARS pipeline into the WindowsAgentArena client:
skill selection and feasibility probing → milestone planning → execution.

The three reasoning roles share `--global-planner-model` (default
`qwen3.8-27b`). GUI tools ask for visual target descriptions and
`--visual-grounder-model` (default `gta1-7b`) resolves them to coordinates.
TARS uses the repository's `mm_agents.llm.AbstractLLM` and the standard
WindowsAgentArena `DesktopEnv`.

Run from the repository root:

```bash
./scripts/run_tars.sh
```

Extra launcher or TARS arguments can be appended, for example:

```bash
./scripts/run_tars.sh --json-name evaluation_examples_windows/test_one.json \
  --tars-reset-wait 0 --tars-evaluation-wait 5
```

Relevant options:

- `--global-planner-model`: gate, planner, and executor model.
- `--visual-grounder-model`: GTA1-compatible point grounder.
- `--tars-reset-wait` / `--tars-evaluation-wait`: waits around execution.
- `--max-steps`: outer TARS action budget.
- `TARS_GATE_AGENT_MAX_STEPS`, `TARS_PLANNER_AGENT_MAX_STEPS`, and
  `TARS_EXECUTOR_AGENT_MAX_STEPS`: role-internal budgets.
- `TARS_MAX_TOKENS`: output budget per model call (default 4096).

Results follow the arena convention under `result_dir/domain/task_id`, with
`result.txt`, `execution_log.json`, `traj.jsonl`, screenshots, and role logs.

Offline checks from `src/win-arena-container/client`:

```bash
python -m unittest mm_agents.tars.test_local -q
```

The adapter changes LocalGUI's Linux guest operations to Windows equivalents:
PowerShell execution, Windows app/window management, Start-menu launching, and
Windows-specific OS skill guidance. Optional web tools require `parallel-web`
and `PARALLEL_API_KEY`; without them TARS receives a tool error and may choose
another route.
