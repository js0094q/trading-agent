# Trading Agent Starter

Minimal, dependency-free runners for two agents:

- **Research Agent**: validates required inputs and produces a daily market prep brief + watchlist.
- **Risk & Position Sizing Agent**: sizes trade plans into executable orders with strict guardrails.

## Structure
- `inputs/` — user-provided config and static inputs (preferences, universe, strategy spec, data source notes).
- `artifacts/signals/` — upstream signal outputs (trade plans, screener).
- `artifacts/research/` — research outputs (`daily_brief.md`, `watchlist.json`).
- `artifacts/sizing/` — sizing outputs (`order_sheet.json`, `risk_checklist.md`).
- `agent_runner.py` — CLI orchestrator for both agents.

## Usage
```bash
# Validate research inputs (writes stub outputs)
./agent_runner.py research --stub

# Size trades (requires equity)
./agent_runner.py sizing --equity 100000
```

Edit `inputs/preferences.json` with real account limits and replace `artifacts/signals/trade_plans.json` with live plans from your signal pipeline before running sizing.
