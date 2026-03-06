# Backtest Analysis

Analyse the backtest results from the implementation above.

If a backtest was run, extract or estimate these metrics:
- Annualised Sharpe ratio
- Maximum drawdown %
- Win rate
- Average holding period
- Number of trades per year

Output JSON:
{"sharpe": 1.2, "max_drawdown": -0.15, "win_rate": 0.52, "trades_per_year": 24, "approved": true, "notes": "..."}

Approved if sharpe >= 1.0 and max_drawdown > -0.25.
If backtest code was not run, estimate from parameters and output approved: false with improvement suggestions.
