"""CLI entrypoint: `ingest` and `ask` subcommands."""

import typer

app = typer.Typer(add_completion=False)


@app.command()
def ingest():
    """Chunk, embed, and upsert the docs corpus into Pinecone."""
    from paymentcopilot.ingestion.ingest import ingest as run_ingest

    typer.echo("Loading, chunking, and embedding docs corpus...")
    num_docs, num_chunks = run_ingest()
    typer.echo(f"Ingested {num_docs} docs -> {num_chunks} chunks -> {num_chunks} vectors upserted.")


@app.command()
def ask(
    query: str,
    top_k: int = typer.Option(5, help="Number of chunks to retrieve."),
    show_chunks: bool = typer.Option(False, "--show-chunks", help="Print raw retrieved chunks and scores."),
):
    """Ask a question and get a grounded, cited answer."""
    from paymentcopilot.generation.generator import generate_answer
    from paymentcopilot.retrieval.retriever import retrieve

    chunks = retrieve(query, top_k=top_k)

    if show_chunks:
        typer.echo("--- Retrieved chunks ---")
        for rc in chunks:
            typer.echo(f"[{rc.score:.4f}] {rc.chunk.source_doc} — {rc.chunk.section}")
        typer.echo("")

    answer = generate_answer(query, chunks)

    typer.echo("--- Answer ---")
    typer.echo(answer.text)
    if not answer.grounded:
        typer.echo("\n(escalation: response was not grounded in retrieved context)")


if __name__ == "__main__":
    app()
