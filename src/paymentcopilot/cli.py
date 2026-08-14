"""CLI entrypoint: `ingest` and `ask` subcommands."""

import typer

app = typer.Typer(add_completion=False)


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


if __name__ == "__main__":
    app()
