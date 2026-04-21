"""Smoke tests for JSONL → DataFrame → report formatters."""

from __future__ import annotations

from pathlib import Path

from quantmetrics_analytics.analysis.event_summary import format_event_summary
from quantmetrics_analytics.analysis.no_trade_analysis import format_no_trade_analysis
from quantmetrics_analytics.analysis.signal_funnel import format_signal_funnel
from quantmetrics_analytics.datasets.decisions import trade_actions_to_decisions_df
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

    assert run(argv=["--jsonl", str(_FIXTURE), "--reports", "summary", "--stdout"]) == 0


def test_cli_default_writes_under_output_rapport(tmp_path: Path, monkeypatch) -> None:
    """Default (no --stdout/--output) writes to repo output_rapport/."""
    import quantmetrics_analytics.cli.run_analysis as ra
    from quantmetrics_analytics.cli.run_analysis import run

    monkeypatch.setattr(ra, "_repo_root", lambda: tmp_path)

    dest_dir = tmp_path / "output_rapport"
    assert run(argv=["--jsonl", str(_FIXTURE), "--reports", "summary"]) == 0
    files = list(dest_dir.glob("*.txt"))
    assert len(files) == 1
    assert "Total events: 5" in files[0].read_text(encoding="utf-8")


def test_trade_actions_to_decisions_df() -> None:
    events = load_events_from_paths([_FIXTURE])
    dec = trade_actions_to_decisions_df(events)
    assert len(dec) == 2
    assert set(dec["decision"].tolist()) == {"NO_ACTION", "ENTER"}


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
            ],
        )
        == 0
    )
    text = out_tsv.read_text(encoding="utf-8")
    assert "decision" in text.splitlines()[0]
    assert "NO_ACTION" in text


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
            ],
        )
        == 0
    )
    assert out_file.is_file()
    assert "Total events: 5" in out_file.read_text(encoding="utf-8")
    assert captured.getvalue() == ""
