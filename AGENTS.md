# Agent Workflows and Commands

## Workflows
- Research agent generates a daily market prep brief and watchlist from inputs and optional screener signals.
- Sizing agent converts trade plans into executable order sizes and a risk checklist based on account equity and limits.

## Commands
```bash
# Validate research inputs (writes stub outputs)
./agent_runner.py research --stub

# Size trades (requires equity)
./agent_runner.py sizing --equity 100000
```

## Notes
- Inputs live in `inputs/` and signal outputs in `artifacts/signals/`.
- Research outputs are written to `artifacts/research/`; sizing outputs go to `artifacts/sizing/`.
