QuantMetrics Analytics

Deterministic analytics engine for event-driven trading systems.

Overview

QuantMetrics Analytics is a downstream analysis module built on top of the QuantMetrics trading infrastructure stack.

It transforms raw event data from QuantLog into structured datasets, actionable insights, and system-level feedback.

This module is not a dashboard or visualization tool.
It is a research and diagnostics engine designed to understand, validate, and improve trading system behavior.

Position in the Quant Stack
Market Data / News
        ↓
QuantBuild (Signal Engine)
        ↓
Risk Engine
        ↓
QuantBridge (Execution Engine)
        ↓
Broker / Trades
        ↓
QuantLog (Event Logging — Source of Truth)
        ↓
QuantMetrics Analytics  ← YOU ARE HERE
        ↓
Insights / Reports / Feedback
        ↓
Strategy Improvements
Core Purpose

The system answers questions such as:

Why are trades not being executed?
Where does the decision pipeline break down?
Which filters reduce or destroy edge?
What is the real expectancy of a strategy?
How does performance vary across regimes and sessions?
How does the system behave under real conditions?
Design Principles
1. QuantLog is the Source of Truth
Raw data is never modified
All analysis is reproducible
Event replay remains deterministic
2. Downstream Intelligence Only
No analytics logic in:
QuantBuild
QuantBridge
QuantLog

All interpretation happens here.

3. Reproducibility

Every analysis result must be:

deterministic
version-controlled
traceable back to raw events
4. Separation of Layers
Raw Events → Structured Data → Entities → Metrics → Insights

Each layer has a single responsibility.

Data Pipeline
QuantLog JSONL (raw events)
        ↓
Ingestion
        ↓
Normalization
        ↓
Bronze (structured events - parquet)
        ↓
Silver (lifecycles & entities)
        ↓
Gold (metrics & aggregates)
        ↓
Reports / Feedback artifacts
Storage Model
analytics_data/

bronze/
  events/

silver/
  signal_cycles/
  trade_lifecycles/

gold/
  metrics/

reports/
  daily/
  runs/
Core Concepts
Signal Cycle

A single decision loop of the strategy:

signal_detected
→ signal_evaluated
→ risk_guard_decision
→ trade_action

Used to understand:

why trades happen
why trades are blocked
Trade Lifecycle

Full execution path:

order_submitted
→ order_filled
→ position_open
→ position_closed

Used to measure:

execution quality
trade performance
MAE / MFE
Position Lifecycle

Lifecycle of an open position:

entry
drawdown (MAE)
expansion (MFE)
exit
Analysis Modules
1. No-Trade Analysis

Breakdown of why trades are not executed:

cooldown_active
regime_blocked
session_blocked
risk_blocked
no_setup
2. Signal Funnel

Pipeline throughput:

Detected → Evaluated → Risk Passed → Executed

Used to identify bottlenecks.

3. Performance Metrics
PnL
PnL (R-multiple)
Expectancy
Winrate
Drawdown
MAE / MFE
4. Contextual Performance

Performance segmented by:

regime (trend / compression / expansion)
session (Asia / London / New York)
strategy
5. System Behaviour Analysis
cooldown effects
filter impact
risk throttling
latency between events
Output Types
Diagnostic Reports (Human)

Readable summaries:

Trades: 0

Top reasons:
- cooldown_active: 64%
- compression_regime: 22%

Insight:
System is over-filtered during NY session.
Feedback Artifacts (Machine)

Structured output for system improvement:

{
  "issue": "low_trade_frequency",
  "root_causes": ["cooldown_active", "compression_regime"],
  "suggestions": [
    "reduce cooldown duration",
    "disable compression trades"
  ]
}
What This Is Not
Not a trading bot
Not a signal generator
Not a dashboard tool
Not a BI platform
What This Is

A research and diagnostics engine for:

validating edge
understanding system behavior
improving trading strategies
enabling a closed feedback loop
Development Approach

The system is built in iterative sprints:

Raw ingestion (JSONL → DataFrame)
No-trade analysis (decision breakdown)
Signal funnel (pipeline diagnostics)
Trade lifecycle (performance)
Context intelligence (edge detection)

Each step is:

directly runnable on real data
incrementally extending the pipeline
Future Direction
automated feedback loops into QuantBuild
strategy optimization suggestions
anomaly detection
multi-strategy portfolio analysis
real-time analytics integration
Philosophy

A trading bot executes trades.
A trading system understands itself.

QuantMetrics Analytics is built to ensure the latter.
