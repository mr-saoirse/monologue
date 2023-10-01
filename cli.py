#!/usr/local/bin/python3
import typer
from monologue import logger 

app = typer.Typer()

 

@app.command("test")
def run_method( message:str = typer.Option(None, "--message", "-m"),):
     logger.log('MEM', message)

     from monologue.entities import AbstractEntity
     from pydantic import Field
     class MyEntity(AbstractEntity):
          code: str = Field(is_key=True)
          created_at: str

     my_entity = MyEntity(code='test', created_at= "2023-01-01")
     logger.log("MEM", f"{message}  {my_entity=}")

    
if __name__ == "__main__":
    app()