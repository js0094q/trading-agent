# RH Execution, External Research Data Stack (Robinhood + “Research Everywhere Else”)

## 1) Core architecture
**Goal:** Keep Robinhood (RH) as your execution venue, and run **research + signals + sizing** off external data feeds that are built for systematic use.

### Split responsibilities
- **Robinhood (execution + accounting)**
  - Place trades manually in RH.
  - Export fills and statements for journaling and performance review.  [oai_citation:0‡Robinhood](https://robinhood.com/support/articles/finding-your-reports-and-statements/?utm_source=chatgpt.com)

- **External market data (research + signals)**
  - Intraday bars, quotes, volume, spreads, VWAP proxies, RVOL, ATR, etc.
  - This drives Agent 1 (prep) and Agent 2 (trade plan triggers).

- **Event risk and catalysts**
  - Macro calendar, earnings flags, upgrades and sector events.
  - This drives “no-trade windows” and “risk-on vs risk-off” context.

---

## 2) Data sources you can actually use (practical list)

### A) Robinhood data you should pull (for journaling and reconciliation)
Use RH to export:
- **Custom account activity reports**
- **Monthly statements**
- Transaction history for fills, timestamps, quantities, prices, fees (if any)  [oai_citation:1‡Robinhood](https://robinhood.com/support/articles/finding-your-reports-and-statements/?utm_source=chatgpt.com)

**Why:** RH exports are your “ground truth” for what you did, useful for P&L attribution and slippage tracking.

---

### B) Intraday market data (for research + signals)
Pick one provider, do not mix providers early, mixing causes timestamp and OHLC inconsistencies.

#### Option 1: Alpaca Market Data (streaming-capable)
- Real-time market data via WebSocket stream is documented and designed for “most up-to-date” updates.  [oai_citation:2‡Alpaca API Docs](https://docs.alpaca.markets/docs/real-time-stock-pricing-data?utm_source=chatgpt.com)  
- Their Market Data API also covers real-time and historical across multiple asset classes.  [oai_citation:3‡Alpaca API Docs](https://docs.alpaca.markets/docs/about-market-data-api?utm_source=chatgpt.com)

**When to choose:** You want streaming bars/quotes and a clean dev experience.

#### Option 2: Polygon (bars and broader coverage)
- Polygon stock data documentation includes aggregate bars (candles), commonly used for intraday timeframes.  [oai_citation:4‡Polygon Documentation](https://polygon.readthedocs.io/en/latest/Stocks.html?utm_source=chatgpt.com)

**When to choose:** You want strong REST coverage and easy “get bars by time range” flows.

**Decision rule:**  
- If you want **streaming**, pick **Alpaca**.  [oai_citation:5‡Alpaca API Docs](https://docs.alpaca.markets/docs/real-time-stock-pricing-data?utm_source=chatgpt.com)  
- If you want mostly **REST bar pulls**, **Polygon** is a straightforward choice.  [oai_citation:6‡Polygon Documentation](https://polygon.readthedocs.io/en/latest/Stocks.html?utm_source=chatgpt.com)

---

### C) Catalysts and scheduled risk (macro + earnings)
You have two workable approaches:

1) **Manual file (fast, reliable):** maintain `inputs/catalysts.json` daily
   - Macro events with time and “no-trade windows”
   - Per-ticker catalysts (earnings, guidance, analyst days)

2) **Calendar/API (more automation):** pick a provider later once your strategy is stable  
   - Start manual to avoid spending time integrating a calendar feed before you have a validated edge.

---

## 3) Recommended “minimum viable stack” (MVS)
This is the simplest configuration that supports the 3-agent pipeline.

### Minimum viable
- **Execution:** RH manual
- **Journaling:** RH export reports/statements  [oai_citation:7‡Robinhood](https://robinhood.com/support/articles/finding-your-reports-and-statements/?utm_source=chatgpt.com)
- **Market data:** Alpaca streaming OR Polygon bars  [oai_citation:8‡Alpaca API Docs](https://docs.alpaca.markets/docs/real-time-stock-pricing-data?utm_source=chatgpt.com)
- **Catalysts:** manual JSON file (initially)

### Why this works
- Agent 1: market prep + watchlist using external intraday bars and liquidity filters
- Agent 2: rule-based triggers from those same bars
- Agent 3: sizing from stop distance + your risk parameters
- RH stays cleanly separated as the execution UI.

---

## 4) What to write into `inputs/data_sources.md`
Use this template:

## Data Sources (single source of truth)
- Execution venue: Robinhood (manual)
- Execution history: Robinhood reports/statements export
- Market data provider: {Alpaca Market Data | Polygon}
- Candles: 1m/5m/15m
- Quote fields: bid/ask or spread proxy, volume, VWAP proxy (if computed)
- Event risk: catalysts.json (manual, daily)

## Constraints
- No scraping behind logins
- No unofficial RH endpoints for trading
- Signals derived only from the market data provider + your catalyst inputs
- RH exports used only for journaling and reconciliation

---

## 5) Next choice you need to make (so your pipeline is coherent)
Pick **one**:
- **Alpaca** (streaming-first)  [oai_citation:9‡Alpaca API Docs](https://docs.alpaca.markets/docs/real-time-stock-pricing-data?utm_source=chatgpt.com)
- **Polygon** (REST-first)  [oai_citation:10‡Polygon Documentation](https://polygon.readthedocs.io/en/latest/Stocks.html?utm_source=chatgpt.com)

If you tell me which you prefer and your timeframe (1m vs 5m), I will:
- finalize a concrete `inputs/data_sources.md`,
- provide the exact CSV schema your Research Agent should expect,
- and update the runner script to pull from that provider (still research-only).