# quantanalyticsv1

Read-only analytics for **JSONL** event files in the same shape as **`quantlogv1`**: turn a day folder, a single file, or a glob of logs into **text reports** (funnel, no-trade reasons, performance, regime). **By default** each run writes a UTF-8 **`.txt`** file under **`output_rapport/`** in this repository (timestamped name). Use **`--stdout`** for console-only output, or **`--output`** / **`-o`** for a custom path. This repo is **downstream only** — it does not place orders, call brokers, or write back to your logs.

Data flow: `quantbuildv1` / `quantbridgev1` → `quantlogv1` (JSONL) → **`quantanalyticsv1`** (reports).

- **Python package (metadata name):** `quantmetrics-analytics`
- **Import:** `import quantmetrics_analytics`
- **CLI:** `python -m quantmetrics_analytics.cli.run_analysis` · `quantmetrics-analytics` (after `pip install`)

---

## What you get

| Report | What it answers |
| --- | --- |
| `summary` | Total events and counts per `event_type` |
| `no-trade` | `trade_action` with `NO_ACTION`: breakdown by canonical `reason` |
| `funnel` | `signal_detected` → `signal_evaluated` → risk `ALLOW` → trade intent (`ENTER` / `REVERSE`), with retention |
| `performance` | Trade / fill counts; aggregates `payload_pnl_r` (and related fields) when present |
| `regime` | Volume by regime/session from `signal_evaluated`; ENTER/REVERSE by regime via `trace_id` when possible |

Pass `--reports section1,section2` or `--reports all`.

---

## Requirements

- Python **≥ 3.10**
- **pandas** ≥ 2.0 (pulled in as a dependency when you install the package)

---

## Install

From a clone of this repository:

```bash
cd quantanalyticsv1    # or your local folder name
pip install -e .
```

Development (tests):

```bash
pip install -e ".[dev]"
pytest -q
```

---

## Quick start

Pick **exactly one** input mode: `--jsonl`, `--dir`, or `--glob`.

### Single file

```bash
python -m quantmetrics_analytics.cli.run_analysis \
  --jsonl /path/to/events.jsonl \
  --reports all
```

Default file location (no extra flags):

```text
quantanalyticsv1/output_rapport/<input_stem>_YYYYMMDD_HHMMSSZ.txt
```

Custom path:

```bash
python -m quantmetrics_analytics.cli.run_analysis \
  --jsonl /path/to/events.jsonl \
  --reports all \
  -o /path/to/reports/analysis.txt
```

Console only (`--stdout`):

```bash
python -m quantmetrics_analytics.cli.run_analysis \
  --jsonl /path/to/events.jsonl \
  --reports summary \
  --stdout
```

### Directory (recursive `*.jsonl`)

```bash
python -m quantmetrics_analytics.cli.run_analysis \
  --dir /path/to/quantlog_day_folder \
  --reports summary,no-trade,funnel
```

### Glob

```bash
python -m quantmetrics_analytics.cli.run_analysis \
  --glob "/path/to/logs/**/*.jsonl" \
  --reports all
```

### Console script

After install, the package also exposes:

```bash
quantmetrics-analytics --jsonl ./events.jsonl --reports summary
```

---

## Documentation

| Doc | Contents |
| --- | --- |
| [docs/ANALYTICS_ARCHITECTURE.md](docs/ANALYTICS_ARCHITECTURE.md) | Reference architecture (bronze / silver / gold, principles, storage) |
| [docs/ANALYTICS_SPRINT_PLAN.md](docs/ANALYTICS_SPRINT_PLAN.md) | Sprint-style roadmap for CLI slices |
| [docs/LIVE_VPS_AND_LOCAL_BACKTEST.md](docs/LIVE_VPS_AND_LOCAL_BACKTEST.md) | Sync JSONL from a VPS, run **`quantbuildv1`** backtests locally, analyze the same `.jsonl` |

---

## Repository layout

```text
quantanalyticsv1/
├── quantmetrics_analytics/
│   ├── ingestion/       JSONL loading (read-only)
│   ├── processing/    normalization → pandas
│   ├── transforms/    silver-layer helpers (e.g. `reconstruct_trades`)
│   ├── analysis/      report modules per slice
│   └── cli/           run_analysis CLI
├── docs/              Architecture, sprint plan, VPS / backtest how-to
├── tests/             Pytest + sample JSONL fixtures
├── pyproject.toml
└── README.md
```

---

## Suite repositories (GitHub)

Events are produced upstream and stored as JSONL in **`quantlogv1`**; contracts live in **`quantlogv1`** / **`quantbuildv1`**. This repo only **reads** JSONL.

| Repo | Remote |
| --- | --- |
| `quantmetrics_os` | [roelofgootjesgit/quantmetrics_os](https://github.com/roelofgootjesgit/quantmetrics_os) |
| `quantbuildv1` | [roelofgootjesgit/quantbuildv1](https://github.com/roelofgootjesgit/quantbuildv1) |
| `quantbridgev1` | [roelofgootjesgit/quantbridgev1](https://github.com/roelofgootjesgit/quantbridgev1) |
| `quantlogv1` | [roelofgootjesgit/quantlogv1](https://github.com/roelofgootjesgit/quantlogv1) |
| `quantanalyticsv1` (**this**) | [roelofgootjesgit/quantanalyticsv1](https://github.com/roelofgootjesgit/quantanalyticsv1) |

---

## License

No `LICENSE` file in the root yet. Add one when you decide how you want to share this code.
