"""CLI entrypoint: `ingest`, `ask`, and `evals` subcommands."""

from pathlib import Path

import typer

app = typer.Typer(add_completion=False)
evals_app = typer.Typer(add_completion=False)
app.add_typer(evals_app, name="evals")

_DEFAULT_GOLDEN_PATH = "data/eval/golden_set.jsonl"
_DEFAULT_EVAL_OUTPUT_DIR = "docs/03-eval-results"


@app.command()
def ingest(
    reset: bool = typer.Option(
        False, "--reset", help="Delete and recreate the Pinecone index before ingesting."
    ),
):
    """Chunk, embed, and upsert the docs (UC1) and policy (UC3) corpora into Pinecone."""
    from paymentcopilot.ingestion.ingest import ingest_all

    typer.echo("Loading, chunking, and embedding docs + policy corpora...")
    result = ingest_all(reset=reset)
    for doc_type, (num_docs, num_chunks) in result.items():
        typer.echo(f"[{doc_type}] {num_docs} docs -> {num_chunks} chunks -> {num_chunks} vectors upserted.")


@app.command()
def ask(
    query: str,
    merchant_id: str = typer.Option(
        "demo-merchant", "--merchant-id", help="Merchant tenant scope for transaction lookups (UC2)."
    ),
    show_route: bool = typer.Option(
        False, "--show-route", help="Print the classified route and reasoning."
    ),
    show_chunks: bool = typer.Option(
        False, "--show-chunks", help="Print raw retrieved chunks and scores."
    ),
):
    """Ask a question — routed to UC1 docs, UC2 transaction lookup, UC3 policy, or refused."""
    from paymentcopilot.graph.router import run_query

    result = run_query(query, merchant_id=merchant_id)

    if show_route:
        typer.echo(f"--- Route: {result.route} ({result.route_reason}) ---")
        if result.guardrail_status != "passed":
            typer.echo(f"--- Guardrail: {result.guardrail_status} ---")

    if show_chunks and result.retrieved_chunks:
        typer.echo("--- Retrieved chunks ---")
        for rc in result.retrieved_chunks:
            typer.echo(f"[{rc.score:.4f}] {rc.chunk.source_doc} — {rc.chunk.section}")
        typer.echo("")

    if result.transaction is not None:
        t = result.transaction
        typer.echo(
            f"--- Transaction {t.txn_id} ({t.status}, {t.amount} {t.currency}, {t.created_at}) ---"
        )

    typer.echo("--- Answer ---")
    typer.echo(result.answer)
    if result.escalated:
        typer.echo("\n(escalated: not answered directly from grounded context)")


@evals_app.command("run")
def evals_run(
    golden_path: str = typer.Option(
        _DEFAULT_GOLDEN_PATH, "--golden-path", help="Golden dataset JSONL file."
    ),
    output_dir: str = typer.Option(
        _DEFAULT_EVAL_OUTPUT_DIR, "--output-dir", help="Directory to write the report pair into."
    ),
    skip_ragas: bool = typer.Option(
        False,
        "--skip-ragas",
        help="Skip RAGAS scoring for a fast iteration loop (refusal-correctness + routing accuracy only).",
    ),
):
    """Run the golden-set eval suite: refusal-correctness, routing accuracy, and (unless --skip-ragas) RAGAS metrics."""
    from datetime import UTC, datetime

    from paymentcopilot.evals.golden_set import load_golden_set
    from paymentcopilot.evals.report import build_report, write_report
    from paymentcopilot.evals.runner import run_golden_set

    golden_path_p = Path(golden_path)
    items = load_golden_set(golden_path_p)
    typer.echo(f"Loaded {len(items)} golden items from {golden_path}. Running...")
    records = run_golden_set(items)

    ragas_scores = None
    if not skip_ragas:
        from paymentcopilot.evals.ragas_eval import run_ragas

        typer.echo("Running RAGAS scoring (this makes many additional Claude calls)...")
        ragas_scores = run_ragas(records)

    run_id = f"eval-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
    markdown, report = build_report(run_id, golden_path, records, skip_ragas, ragas_scores)
    md_path, json_path = write_report(Path(output_dir), run_id, markdown, report)

    refusal = report["refusal_correctness"]
    routing = report["routing_accuracy"]
    typer.echo(
        f"Refusal correctness: precision={refusal['precision']:.3f} recall={refusal['recall']:.3f} "
        f"f1={refusal['f1']:.3f} accuracy={refusal['accuracy']:.3f}"
    )
    typer.echo(f"Routing accuracy: {routing['correct']}/{routing['total']} ({routing['accuracy']:.3f})")
    if ragas_scores:
        typer.echo(f"RAGAS: {', '.join(f'{k}={v:.3f}' for k, v in sorted(ragas_scores.items()))}")
    typer.echo(f"Failing items: {len(report['failing_items'])}")
    typer.echo(f"Report written to {md_path} and {json_path}")


@evals_app.command("sweep-thresholds")
def evals_sweep_thresholds(
    golden_path: str = typer.Option(
        _DEFAULT_GOLDEN_PATH, "--golden-path", help="Golden dataset JSONL file."
    ),
    uc1_candidates: str = typer.Option(
        "0.30,0.35,0.40,0.45,0.50", "--uc1-candidates", help="Comma-separated UC1 threshold candidates."
    ),
    uc3_candidates: str = typer.Option(
        "0.35,0.40,0.45,0.50,0.55", "--uc3-candidates", help="Comma-separated UC3 threshold candidates."
    ),
):
    """Manual, occasional-run tool: re-run UC1/UC3 golden items at each candidate confidence
    threshold and compare refusal-correctness (PRD §14)."""
    from paymentcopilot.evals.golden_set import load_golden_set
    from paymentcopilot.evals.threshold_sweep import (
        parse_candidates,
        sweep_uc1_thresholds,
        sweep_uc3_thresholds,
    )

    items = load_golden_set(Path(golden_path))

    typer.echo("UC1_CONFIDENCE_THRESHOLD sweep:")
    for candidate, m in sweep_uc1_thresholds(items, parse_candidates(uc1_candidates)):
        typer.echo(
            f"  {candidate:.2f}: precision={m.precision:.3f} recall={m.recall:.3f} "
            f"f1={m.f1:.3f} accuracy={m.accuracy:.3f}"
        )

    typer.echo("UC3_CONFIDENCE_THRESHOLD sweep:")
    for candidate, m in sweep_uc3_thresholds(items, parse_candidates(uc3_candidates)):
        typer.echo(
            f"  {candidate:.2f}: precision={m.precision:.3f} recall={m.recall:.3f} "
            f"f1={m.f1:.3f} accuracy={m.accuracy:.3f}"
        )


if __name__ == "__main__":
    app()
