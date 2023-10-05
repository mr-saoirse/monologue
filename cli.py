#!/usr/local/bin/python3
import typer
from monologue import logger
from monologue.core.spaces import LogProcessor

app = typer.Typer()

data_generator_app = typer.Typer()
app.add_typer(data_generator_app, name="generate")


@app.command("test")
def run_method(
    message: str = typer.Option(None, "--message", "-m"),
):
    """
    Method to test the logging output
    """

    logger.log("EVENT", message)

    from monologue.entities import AbstractEntity
    from pydantic import Field

    class MyEntity(AbstractEntity):
        code: str = Field(is_key=True)
        created_at: str

    my_entity = MyEntity(code="test", created_at="2023-01-01")
    logger.log("EVENT", f"{message}  {my_entity=}")


@data_generator_app.command("book_reviews")
def run_method(
    limit: int = typer.Option(10, "--limit", "-l"),
):
    from monologue.entities.examples.MyriadLoggers import ingest_book_reviewers_sample

    ingest_book_reviewers_sample(limit=limit)


@app.command("ingest")
def run_method(
    input_file: str = typer.Option(None, "--file", "-f"),
    use_loki_file: str = typer.Option(None, "--loki", "-l"),
    limit: int = typer.Option(None, "--limit", "-l"),
):
    """
    we consume whatever we are given into memory for now and assume we can deal with it for testing

    """
    if input_file:
        proc = LogProcessor()
        i = 0
        with open(input_file) as f:
            # we can implement some sort of batching or queuing here later
            for line in LogProcessor.log_lines_generator(f.read()):
                # print(line)
                # print("<<>>")
                proc.process_line(line)
                i += 1
                if limit and i > limit:
                    break


if __name__ == "__main__":
    app()
