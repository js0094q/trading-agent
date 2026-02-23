# Trading Ruleset (US equities • Cash • 5m • RTH • ~30 min holds)

## Universe & Session
- **Market:** US equities (stocks and ETFs only)
- **Session:** **RTH only** (no pre/after-hours entries)
- **Allowed instruments:** stocks
- **Disallowed:** 0DTE options, leveraged ETFs

## Portfolio Constraints
- **Account type:** cash (use **settled cash** only)
- **Max open positions:** **2**
- **Correlation rule:** if 2 positions are correlated (same sector/theme/index driver), **split risk** (see Risk section)

## Risk Management
- **Max risk per trade:** **0.5% of account equity**
- **Max daily loss:** **2.0%** *(hard stop: stop trading for the day once hit)*
- **Max total concurrent risk:** **0.5%**
  - If holding **2 positions**, risk **0.25% each** (unless clearly uncorrelated)

## Position Sizing (Required Before Entry)
- Stop must be defined **at entry**
- **No widening stops**
- **Shares = (Equity × 0.005) ÷ |Entry − Stop|**
  - Use the absolute dollar stop distance
- If stop distance is too tight for normal 5m noise, **reduce size** or **skip**

## Trade Management (5m • ~30 minutes)
- **Primary chart:** 5m
- **Intended max holding time:** ~**30 minutes**
- **Time stop:** exit any position still open at **+30 minutes** unless:
  - you have a predefined “hold extension” rule (e.g., trend + trailing stop)
- **Cooldown:** after **2 consecutive losses**, pause trading for **15 minutes** (or until a new fully qualified setup appears)

## Execution & Liquidity Filters
- **Slippage assumption:** **2 bps** (baseline)
- Trade only stocks with **tight spreads** and **strong intraday volume**
- Avoid entries when spread is unusually wide for the stock, especially around sudden volatility

## Event / News Risk
- No new entries:
  - during major scheduled macro releases (use your consistent buffer window)
  - immediately after halts/resumptions unless that’s explicitly your strategy
- Optional: avoid initiating trades in stocks **reporting earnings that day** unless you have a specific earnings plan

## Daily Process
- **Done-for-the-day conditions:**
  - Daily realized P&L hits **−2.0%**
  - Any rule breach
- Log each trade: setup, entry, stop, size, exit reason (stop/target/time stop/manual), and rule adherence