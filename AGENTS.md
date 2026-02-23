# Agent Workflows and Commands

## Plan / Signal Agent (trade-plan completion)
- Goal: ensure every trade plan has concrete `entry_price` and `stop_price` so sizing can proceed.
- Inputs: `artifacts/signals/trade_plans.json`
- Behavior: pulls live quotes (Yahoo batch; Stooq fallback) and applies configurable buffers (default +0.10% entry, 1.0% stop distance). Appends an inference note to each auto-filled plan.
- Guardrails: best-effort only; if a quote is unavailable, leave the plan untouched and report the symbol.
- Output: updates `artifacts/signals/trade_plans.json` in place with filled prices.

## Research Agent (daily market prep)
- Goal: regime read, catalysts, key levels, filtered watchlist.
- Inputs: `inputs/preferences.json`, `inputs/universe.txt`, `inputs/strategy_spec.md`, `inputs/data_sources.md`; optional `artifacts/signals/screener.json`.
- Guardrails: educational only; no trades/APIs; if any required input missing/empty, stop and report instead of guessing.
- Outputs: `artifacts/research/daily_brief.md` (regime, volatility, liquidity, catalysts, watchlist rationale) and `artifacts/research/watchlist.json` (bias, thesis, key_levels, notes per symbol).
- Process: load inputs → derive regime/vol/liquidity from provided data → fold catalysts if supplied → rank watchlist by liquidity/clean levels/catalyst fit → write both outputs; mark inference explicitly; done only when both files exist (or note no symbols qualified).

## Sizing Agent (risk & position sizing)
- Goal: convert trade plans into executable order sizes and risk controls with zero ambiguity.
- Required inputs: `account_equity_usd`, risk limits from `inputs/preferences.json` (max_risk_per_trade_pct, max_daily_loss_pct, max_positions, max_total_concurrent_risk_pct), trade plans `artifacts/signals/trade_plans.json`; optional per-instrument constraints (max_shares, no_short, lot_size, max_notional).
- Rules: reject plans missing entry/stop or non-positive stop distance; `risk_per_trade_usd = equity * max_risk_per_trade_pct`; `size_units = risk_per_trade_usd / |entry - stop|`; round down to tradable unit; enforce instrument and portfolio caps; if size < 1 unit, mark "skip: stop too tight"; no leverage assumptions unless provided.
- Outputs: `artifacts/sizing/order_sheet.json` (direction, entry, stop, risk_per_trade_usd, unit_size/type, max_loss_if_stopped, notes) and `artifacts/sizing/risk_checklist.md` (daily stop, circuit breakers, max trades, skips/violations).
- Process: validate required inputs → per-plan validation and sizing → apply portfolio/instrument constraints → write both outputs; success only when every plan is sized or explicitly skipped.

## Commands
```bash
# Fill missing entry/stop using live quotes (defaults: +0.10% entry buffer, 1.0% stop distance)
./agent_runner.py plan --entry-buffer-pct 0.10 --stop-pct 1.0

# Validate research inputs (writes stub outputs)
./agent_runner.py research --stub

# Size trades (requires equity)
./agent_runner.py sizing --equity 100000
```

## Notes
- Inputs live in `inputs/` and signal outputs in `artifacts/signals/`.
- Research outputs write to `artifacts/research/`; sizing outputs to `artifacts/sizing/`.
