#!/usr/bin/env python3
"""
Minimal orchestrator for the two trading agents:
- research: validates required inputs and (optionally) writes stub outputs
- sizing: computes position sizes from trade_plans.json with strict guardrails

Defaults are intentionally strict: if any required input is missing or invalid,
the command halts with an explicit message instead of guessing.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).parent.resolve()
INPUTS = BASE_DIR / "inputs"
ARTIFACTS = BASE_DIR / "artifacts"


def read_json(path: Path) -> Any:
    """Load JSON, raising a ValueError with context on failure."""
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise ValueError(f"Missing file: {path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e


def ensure_nonempty(paths: List[Path]) -> List[Path]:
    """Return list of missing or empty paths."""
    missing = []
    for p in paths:
        if not p.exists() or p.stat().st_size == 0:
            missing.append(p)
    return missing


# ---------- Research Agent ----------

def run_research(args: argparse.Namespace) -> int:
    required = [
        INPUTS / "preferences.json",
        INPUTS / "universe.txt",
        INPUTS / "strategy_spec.md",
        INPUTS / "data_sources.md",
    ]
    missing = ensure_nonempty(required)
    if missing:
        print("Research agent halted. Missing or empty files:")
        for m in missing:
            print(f"- {m}")
        return 1

    # Optional screener; just warn if absent.
    screener_path = ARTIFACTS / "signals" / "screener.json"
    if not screener_path.exists():
        print("Note: optional screener not found; continuing without it.")

    if args.stub:
        out_dir = ARTIFACTS / "research"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "daily_brief.md").write_text(
            "# Daily Market Prep (stub)\n\n"
            "- Status: inputs validated; replace this stub with real analysis.\n",
            encoding="utf-8",
        )
        (out_dir / "watchlist.json").write_text("[]\n", encoding="utf-8")
        print(f"Wrote stub outputs to {out_dir}")
    else:
        print("Inputs validated. Add your research logic and write outputs to:")
        print(f"- {ARTIFACTS / 'research' / 'daily_brief.md'}")
        print(f"- {ARTIFACTS / 'research' / 'watchlist.json'}")
    return 0


# ---------- Sizing Agent ----------

def validate_limits(prefs: Dict[str, Any]) -> Dict[str, float]:
    required_keys = [
        "max_risk_per_trade_pct",
        "max_daily_loss_pct",
        "max_positions",
        "max_total_concurrent_risk_pct",
    ]
    missing = [k for k in required_keys if k not in prefs]
    if missing:
        raise ValueError(f"preferences.json missing keys: {', '.join(missing)}")

    limits = {
        "max_risk_per_trade_pct": float(prefs["max_risk_per_trade_pct"]),
        "max_daily_loss_pct": float(prefs["max_daily_loss_pct"]),
        "max_positions": int(prefs["max_positions"]),
        "max_total_concurrent_risk_pct": float(
            prefs["max_total_concurrent_risk_pct"]
        ),
    }
    return limits


def clamp_to_notional(size_units: float, entry: float, max_notional: float) -> float:
    if max_notional <= 0:
        return size_units
    max_units = math.floor(max_notional / entry)
    return max(0, min(size_units, max_units))


def run_sizing(args: argparse.Namespace) -> int:
    required = [ARTIFACTS / "signals" / "trade_plans.json"]
    missing = ensure_nonempty(required)
    if missing:
        print("Sizing agent halted. Missing or empty files:")
        for m in missing:
            print(f"- {m}")
        return 1

    if args.equity is None:
        print("Sizing agent halted. Provide account equity via --equity.")
        return 1
    equity = float(args.equity)

    prefs_path = INPUTS / "preferences.json"
    try:
        prefs = read_json(prefs_path)
    except ValueError as e:
        print(f"Sizing agent halted. {e}")
        return 1

    try:
        limits = validate_limits(prefs)
    except ValueError as e:
        print(f"Sizing agent halted. {e}")
        return 1

    try:
        trade_plans = read_json(ARTIFACTS / "signals" / "trade_plans.json")
    except ValueError as e:
        print(f"Sizing agent halted. {e}")
        return 1

    if not isinstance(trade_plans, list):
        print("Sizing agent halted. trade_plans.json must be a list of plans.")
        return 1

    planned_positions = max(1, len(trade_plans))
    # Split risk if multiple positions are planned to respect total concurrent cap.
    risk_per_trade_pct = min(
        limits["max_risk_per_trade_pct"],
        limits["max_total_concurrent_risk_pct"] / planned_positions,
    )
    risk_per_trade_usd = equity * risk_per_trade_pct
    max_total_risk_usd = equity * limits["max_total_concurrent_risk_pct"]

    sized_orders = []
    skipped = []
    total_risk = 0.0

    for plan in trade_plans:
        symbol = plan.get("symbol", "")
        entry = plan.get("entry_price")
        stop = plan.get("stop_price")
        direction = plan.get("direction", "").lower()
        lot_size = plan.get("lot_size", 1)
        max_shares = plan.get("max_shares")
        max_notional = plan.get("max_notional")
        no_short = plan.get("no_short", False)
        notes = []

        if entry is None or stop is None:
            skipped.append((symbol, "missing entry or stop"))
            continue
        stop_dist = abs(entry - stop)
        if stop_dist <= 0:
            skipped.append((symbol, "stop distance <= 0"))
            continue
        if direction not in ("long", "short"):
            skipped.append((symbol, "direction must be 'long' or 'short'"))
            continue
        if direction == "short" and no_short:
            skipped.append((symbol, "shorting disabled for instrument"))
            continue

        raw_units = risk_per_trade_usd / stop_dist
        sized_units = math.floor(raw_units / lot_size) * lot_size
        if max_shares is not None:
            sized_units = min(sized_units, int(max_shares))
        if max_notional is not None:
            sized_units = clamp_to_notional(sized_units, entry, float(max_notional))

        if sized_units < 1:
            skipped.append((symbol, "size < 1 unit; stop too tight"))
            continue

        max_loss = sized_units * stop_dist
        total_risk += max_loss

        sized_orders.append(
            {
                "symbol": symbol,
                "direction": direction,
                "entry": plan.get("entry"),
                "stop": stop,
                "risk_per_trade_usd": round(risk_per_trade_usd, 2),
                "unit_size": int(sized_units),
                "unit_type": plan.get("unit_type", "shares"),
                "max_loss_if_stopped": round(max_loss, 2),
                "notes": "; ".join(notes) if notes else "",
            }
        )

    if len(sized_orders) > limits["max_positions"]:
        # Keep first N, skip the rest to preserve deterministic order.
        extra = sized_orders[limits["max_positions"] :]
        sized_orders = sized_orders[: limits["max_positions"]]
        for o in extra:
            skipped.append((o["symbol"], "exceeds max_positions"))

    if total_risk > max_total_risk_usd:
        skipped.append(
            (
                "<aggregate>",
                f"total risk {total_risk:.2f} exceeds limit {max_total_risk_usd:.2f}",
            )
        )

    out_dir = ARTIFACTS / "sizing"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "order_sheet.json").write_text(
        json.dumps(sized_orders, indent=2), encoding="utf-8"
    )

    checklist_lines = [
        "# Risk Checklist",
        f"- Account equity: {equity}",
        f"- Max risk per trade: {limits['max_risk_per_trade_pct']*100:.2f}%",
        f"- Max daily loss: {limits['max_daily_loss_pct']*100:.2f}%",
        f"- Max positions: {limits['max_positions']}",
        f"- Max total concurrent risk: {limits['max_total_concurrent_risk_pct']*100:.2f}%",
        "",
        "## Skipped / Notes",
    ]
    if skipped:
        for sym, reason in skipped:
            checklist_lines.append(f"- {sym}: {reason}")
    else:
        checklist_lines.append("- None")

    (out_dir / "risk_checklist.md").write_text(
        "\n".join(checklist_lines) + "\n", encoding="utf-8"
    )

    print(f"Wrote {out_dir / 'order_sheet.json'}")
    print(f"Wrote {out_dir / 'risk_checklist.md'}")
    if skipped:
        print("Skipped items:")
        for sym, reason in skipped:
            print(f"- {sym}: {reason}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Starter runner for research and sizing agents."
    )
    sub = parser.add_subparsers(dest="cmd")

    p_research = sub.add_parser("research", help="validate inputs for research agent")
    p_research.add_argument(
        "--stub",
        action="store_true",
        help="write stub outputs after validation",
    )

    p_sizing = sub.add_parser(
        "sizing", help="compute position sizes from trade_plans.json"
    )
    p_sizing.add_argument(
        "--equity",
        type=float,
        help="account equity in USD (required)",
    )

    args = parser.parse_args()
    if args.cmd == "research":
        return run_research(args)
    if args.cmd == "sizing":
        return run_sizing(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
