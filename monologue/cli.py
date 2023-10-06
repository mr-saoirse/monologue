#!/usr/local/bin/python3
import typer
import typing
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
    input_file: str = typer.Option(None, "--file", "-f"),
    limit: int = typer.Option(10, "--limit", "-l"),
):
    from monologue.entities.examples.MyriadLoggers import ingest_book_reviewers_sample

    ingest_book_reviewers_sample(input_file=input_file, limit=limit)


@app.command("ingest")
def run_method(
    input_file: str = typer.Option(None, "--file", "-f"),
    use_loki: typing.Optional[str] = typer.Option(False, "--loki", "-l"),
    limit: int = typer.Option(None, "--limit", "-l"),
):
    """
    we consume whatever we are given into memory for now and assume we can deal with it for testing

    """
    proc = LogProcessor()
    if use_loki:
        logger.info("Consuming logs from loki")
        from monologue.core.data.clients import LokiClient

        c = LokiClient()
        while True:
            # no error handling - lets see what breaks
            log_info_collection = c.query('{pod="monologue"}', try_parse=True)

            for log_info in log_info_collection:
                # we need to handle multiline log splits here
                for log_line in LogProcessor.log_lines_generator_from_generator(
                    log_info
                ):
                    try:
                        proc.process_line(log_line)
                    except:
                        raise
                        logger.error(f"Parsing failed {log_line=}")

    elif input_file:
        logger.info("Consuming logs from file")

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
