"""Smoke tests for JSONL → DataFrame → report formatters."""

from __future__ import annotations

import shutil
from pathlib import Path

from quantmetrics_analytics.analysis.event_summary import format_event_summary
from quantmetrics_analytics.analysis.no_trade_analysis import format_no_trade_analysis
from quantmetrics_analytics.analysis.signal_funnel import format_signal_funnel, signal_funnel_metrics_dict
from quantmetrics_analytics.datasets.closed_trades import trade_closed_events_to_df
from quantmetrics_analytics.datasets.decisions import trade_actions_to_decisions_df
from quantmetrics_analytics.datasets.executions import execution_events_to_df
from quantmetrics_analytics.datasets.guard_decisions import risk_guard_events_to_df
from quantmetrics_analytics.ingestion.jsonl import load_events_from_paths
from quantmetrics_analytics.processing.normalize import events_to_dataframe

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_events.jsonl"


def test_load_normalize_summary() -> None:
    events = load_events_from_paths([_FIXTURE])
    df = events_to_dataframe(events)
    assert len(df) == 5
    assert "payload_decision" in df.columns
    text = format_event_summary(df)
    assert "Total events: 5" in text
    assert "trade_action" in text


def test_no_trade_and_funnel() -> None:
    events = load_events_from_paths([_FIXTURE])
    df = events_to_dataframe(events)
    nt = format_no_trade_analysis(df)
    assert "cooldown_active" in nt
    assert "NO_ACTION" in nt or "NO_ACTION events" in nt
    fn = format_signal_funnel(df)
    assert "signal_detected" in fn
    assert "ENTER/REVERSE" in fn


def test_cli_exit_code(tmp_path: Path) -> None:
    from quantmetrics_analytics.cli.run_analysis import run

    assert run(argv=["--jsonl", str(_FIXTURE), "--reports", "summary", "--stdout", "--no-key-findings-md"]) == 0


def test_cli_default_quantlog_input_sibling_quantbuild(tmp_path: Path, monkeypatch) -> None:
    """With no --jsonl/--glob/--dir, read QuantBuild default quantlog folder when present."""
    import quantmetrics_analytics.cli.run_analysis as ra
    from quantmetrics_analytics.cli.run_analysis import run

    monkeypatch.chdir(tmp_path)
    ql = tmp_path / "quantbuildv1" / "data" / "quantlog_events"
    ql.mkdir(parents=True)
    shutil.copy(_FIXTURE, ql / "backtest.jsonl")
    out_rap = tmp_path / "output_rapport"
    monkeypatch.setattr(ra, "_output_rapport_dir", lambda: out_rap)

    assert run(argv=["--reports", "summary", "--no-key-findings-md"]) == 0
    files = list(out_rap.glob("*.txt"))
    assert len(files) == 1
    assert "Total events: 5" in files[0].read_text(encoding="utf-8")


def test_cli_default_writes_under_output_rapport(tmp_path: Path, monkeypatch) -> None:
    """Default (no --stdout/--output) writes to repo output_rapport/."""
    import quantmetrics_analytics.cli.run_analysis as ra
    from quantmetrics_analytics.cli.run_analysis import run

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(ra, "_repo_root", lambda: tmp_path)

    dest_dir = tmp_path / "output_rapport"
    assert run(argv=["--jsonl", str(_FIXTURE), "--reports", "summary", "--no-key-findings-md"]) == 0
    files = list(dest_dir.glob("*.txt"))
    assert len(files) == 1
    assert "Total events: 5" in files[0].read_text(encoding="utf-8")


def test_cli_writes_key_findings_md_next_to_report(tmp_path: Path, monkeypatch) -> None:
    """Default run writes ``<report_stem>_KEY_FINDINGS.md`` paired with the .txt report."""
    import quantmetrics_analytics.cli.run_analysis as ra
    from quantmetrics_analytics.cli.run_analysis import run

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(ra, "_repo_root", lambda: tmp_path)

    dest_dir = tmp_path / "output_rapport"
    assert run(argv=["--jsonl", str(_FIXTURE), "--reports", "summary"]) == 0
    txts = sorted(dest_dir.glob("*.txt"))
    kfs = sorted(dest_dir.glob("*_KEY_FINDINGS.md"))
    assert len(txts) == 1
    assert len(kfs) == 1
    assert kfs[0].stem == f"{txts[0].stem}_KEY_FINDINGS"
    md = kfs[0].read_text(encoding="utf-8")
    assert md.startswith("# Key findings")
    assert "## Warnings" in md
    assert "## Headline" in md


def test_trade_actions_to_decisions_df() -> None:
    events = load_events_from_paths([_FIXTURE])
    dec = trade_actions_to_decisions_df(events)
    assert len(dec) == 2
    assert set(dec["decision"].tolist()) == {"NO_ACTION", "ENTER"}


def test_guard_executions_closed_exports_and_summary(tmp_path: Path) -> None:
    from quantmetrics_analytics.analysis.run_summary import build_run_summary
    from quantmetrics_analytics.cli.run_analysis import run

    events = load_events_from_paths([_FIXTURE])
    gdf = risk_guard_events_to_df(events)
    assert len(gdf) == 1
    assert gdf.iloc[0]["guard_name"] == "size"
    cdf = trade_closed_events_to_df(events)
    assert len(cdf) == 0
    edf = execution_events_to_df(events)
    assert len(edf) == 0

    summary = build_run_summary(events=events, df=events_to_dataframe(events), input_paths=[_FIXTURE])
    assert summary["totals"]["events_loaded"] == 5
    assert "signal_detected" in summary["signal_funnel"]
    assert "data_quality" in summary and "event_counts" in summary["data_quality"]
    assert "decision_cycle_funnel" in summary
    assert "key_findings" in summary and "headline" in summary["key_findings"]
    assert "analytics_warnings" in summary

    out_json = tmp_path / "rs.json"
    out_md = tmp_path / "rs.md"
    assert (
        run(
            argv=[
                "--jsonl",
                str(_FIXTURE),
                "--reports",
                "summary",
                "--stdout",
                "--run-summary-json",
                str(out_json),
                "--run-summary-md",
                str(out_md),
                "--export-guard-tsv",
                str(tmp_path / "g.tsv"),
                "--no-key-findings-md",
            ],
        )
        == 0
    )
    assert out_json.is_file()
    assert "signal_funnel" in out_json.read_text(encoding="utf-8")
    md_text = out_md.read_text(encoding="utf-8")
    assert md_text.startswith("# Run summary")
    assert "## Data quality" in md_text


def test_signal_funnel_metrics_dict() -> None:
    events = load_events_from_paths([_FIXTURE])
    df = events_to_dataframe(events)
    m = signal_funnel_metrics_dict(df)
    assert m["signal_detected"] >= 1
    assert any(str(k).startswith("pct_retained") for k in m)


def test_cli_export_decisions_tsv(tmp_path: Path) -> None:
    from quantmetrics_analytics.cli.run_analysis import run

    out_tsv = tmp_path / "decisions.tsv"
    assert (
        run(
            argv=[
                "--jsonl",
                str(_FIXTURE),
                "--reports",
                "summary",
                "--stdout",
                "--export-decisions-tsv",
                str(out_tsv),
                "--no-key-findings-md",
            ],
        )
        == 0
    )
    text = out_tsv.read_text(encoding="utf-8")
    assert "decision" in text.splitlines()[0]
    assert "NO_ACTION" in text


def test_cli_research_report_stdout() -> None:
    from io import StringIO

    from quantmetrics_analytics.cli.run_analysis import run

    buf = StringIO()
    assert run(
        stdout=buf,
        argv=["--jsonl", str(_FIXTURE), "--reports", "research", "--stdout", "--no-key-findings-md"],
    ) == 0
    out = buf.getvalue()
    assert "RESEARCH DIAGNOSTICS" in out
    assert "DATA QUALITY" in out


def test_cli_writes_output_file(tmp_path: Path) -> None:
    from io import StringIO

    from quantmetrics_analytics.cli.run_analysis import run

    out_file = tmp_path / "nested" / "report.txt"
    captured = StringIO()
    assert (
        run(
            stdout=captured,
            argv=[
                "--jsonl",
                str(_FIXTURE),
                "--reports",
                "summary",
                "--output",
                str(out_file),
                "--no-key-findings-md",
            ],
        )
        == 0
    )
    assert out_file.is_file()
    assert "Total events: 5" in out_file.read_text(encoding="utf-8")
    assert captured.getvalue() == ""
