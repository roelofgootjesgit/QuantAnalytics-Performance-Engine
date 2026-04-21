"""CLI: load QuantLog JSONL and print analytics sections (read-only)."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from quantmetrics_analytics.analysis.event_summary import format_event_summary
from quantmetrics_analytics.analysis.no_trade_analysis import format_no_trade_analysis
from quantmetrics_analytics.analysis.performance_summary import format_performance_summary
from quantmetrics_analytics.analysis.regime_performance import format_regime_performance
from quantmetrics_analytics.analysis.signal_funnel import format_signal_funnel
from quantmetrics_analytics.datasets.decisions import trade_actions_to_decisions_df
from quantmetrics_analytics.ingestion.jsonl import load_events_from_paths
from quantmetrics_analytics.processing.normalize import events_to_dataframe

_VALID_REPORTS = frozenset({"summary", "no-trade", "funnel", "performance", "regime"})


def _parse_reports(spec: str) -> list[str]:
    s = spec.strip().lower()
    if s == "all":
        return ["summary", "no-trade", "funnel", "performance", "regime"]
    parts = [p.strip().lower() for p in spec.split(",") if p.strip()]
    bad = [p for p in parts if p not in _VALID_REPORTS]
    if bad:
        raise ValueError(f"Unknown report(s): {bad}. Valid: {sorted(_VALID_REPORTS)} or all")
    return parts


def _collect_paths(args: argparse.Namespace) -> list[Path]:
    if getattr(args, "jsonl", None):
        p = args.jsonl.expanduser().resolve()
        return [p] if p.is_file() else []
    if getattr(args, "glob_pattern", None):
        from glob import glob

        paths = sorted(Path(p).expanduser().resolve() for p in glob(args.glob_pattern))
        return [p for p in paths if p.is_file()]
    if getattr(args, "dir", None):
        d = args.dir.expanduser().resolve()
        if not d.is_dir():
            return []
        return sorted({p for p in d.rglob("*.jsonl") if p.is_file()})
    return []


def _repo_root() -> Path:
    """Repository root (folder that contains `quantmetrics_analytics/`)."""
    return Path(__file__).resolve().parents[2]


def _safe_filename_part(raw: str, *, max_len: int = 72) -> str:
    out = "".join(c if c.isalnum() or c in "-_" else "_" for c in raw)
    out = out.strip("_")[:max_len].strip("_")
    return out or "report"


def _default_report_path(args: argparse.Namespace, paths: list[Path]) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    out_dir = _repo_root() / "output_rapport"
    if getattr(args, "jsonl", None):
        stem = _safe_filename_part(paths[0].stem) if paths else "report"
        name = f"{stem}_{ts}.txt"
    elif getattr(args, "glob_pattern", None):
        name = f"glob_{len(paths)}_files_{ts}.txt"
    else:
        stem = _safe_filename_part(Path(args.dir).resolve().name)
        name = f"{stem}_{ts}.txt"
    return out_dir / name


def run(stdout=sys.stdout, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "QuantMetrics Analytics: QuantLog JSONL reports (read-only). "
            "By default writes UTF-8 text under output_rapport/ in this repo."
        ),
    )
    parser.add_argument(
        "--jsonl",
        type=Path,
        metavar="PATH",
        help="Single JSONL file",
    )
    parser.add_argument(
        "--glob",
        dest="glob_pattern",
        metavar="PATTERN",
        help='Glob pattern e.g. "logs/**/*.jsonl"',
    )
    parser.add_argument(
        "--dir",
        type=Path,
        metavar="DIR",
        help="Directory: include all *.jsonl recursively",
    )
    parser.add_argument(
        "--reports",
        default="all",
        metavar="LIST",
        help=(
            "Comma-separated sections or 'all'. "
            "Choices: summary, no-trade, funnel, performance, regime."
        ),
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        metavar="PATH",
        help=(
            "Write the report to this explicit path (UTF-8). "
            "Overrides the default output_rapport/ file. "
            "Confirmation is printed on stderr."
        ),
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the report to stdout instead of creating a file under output_rapport/.",
    )
    parser.add_argument(
        "--export-decisions-tsv",
        type=Path,
        metavar="PATH",
        help="Also write QuantBuild trade_action rows as TSV (decisions grain MVP).",
    )
    args = parser.parse_args(argv)

    inputs = sum(
        1 for k in ("jsonl", "glob_pattern", "dir") if getattr(args, k, None) is not None
    )
    if inputs != 1:
        parser.error("Specify exactly one of: --jsonl, --glob, --dir")

    try:
        reports = _parse_reports(args.reports)
    except ValueError as exc:
        parser.error(str(exc))

    if getattr(args, "stdout", False) and getattr(args, "output", None) is not None:
        parser.error("Choose either --stdout or --output/-o, not both.")

    paths = _collect_paths(args)
    if not paths:
        print("No JSONL files found (check path / glob / directory).", file=sys.stderr)
        return 2

    events = load_events_from_paths(paths)
    df = events_to_dataframe(events)

    export_path = getattr(args, "export_decisions_tsv", None)
    if export_path is not None:
        dec = trade_actions_to_decisions_df(events)
        export_dest = export_path.expanduser().resolve()
        export_dest.parent.mkdir(parents=True, exist_ok=True)
        dec.to_csv(export_dest, sep="\t", index=False, encoding="utf-8")
        print(f"Decisions TSV written to: {export_dest}", file=sys.stderr)

    blocks: list[str] = []
    for name in reports:
        if name == "summary":
            blocks.append(format_event_summary(df))
        elif name == "no-trade":
            blocks.append(format_no_trade_analysis(df))
        elif name == "funnel":
            blocks.append(format_signal_funnel(df))
        elif name == "performance":
            blocks.append(format_performance_summary(df))
        elif name == "regime":
            blocks.append(format_regime_performance(df))

    text = "\n".join(blocks)

    if getattr(args, "stdout", False):
        print(text, file=stdout, end="")
        return 0

    dest: Path | None
    explicit = getattr(args, "output", None)
    if explicit is not None:
        dest = explicit.expanduser().resolve()
    else:
        dest = _default_report_path(args, paths).resolve()

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    print(f"Report written to: {dest}", file=sys.stderr)
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
