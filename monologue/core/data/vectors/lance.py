"""
A wrapper around to get to know the interface and do some opinionated stuff

https://github.com/lancedb/lance
https://blog.lancedb.com/
https://lancedb.github.io/lance/read_and_write.html
https://lancedb.github.io/lancedb/basic/#creating-an-empty-table
https://lancedb.github.io/lance/notebooks/quickstart.html

"""

from monologue import S3BUCKET
import lance
from monologue.core.data.clients import DuckDBClient
import pyarrow as pa
import typing

VECTOR_STORE_ROOT_URI = f"s3://{S3BUCKET}/stores/vector/v0"

class LanceDataSet:
    def __init__(self, name, space=None, schema=None):
        self._name = name
        self._uri = f"{VECTOR_STORE_ROOT_URI}/{space}/{name}.lance" if space else  f"{VECTOR_STORE_ROOT_URI}/{name}.lance"
        self._dataset = lance.dataset(self._uri)
        self._duck_client = DuckDBClient()
        
    @staticmethod
    def table_from_schema(name, schema, space=None):
        """
        not sure how i want to do this yet but we can create tables from schema
        might be easier to just assume we have some data at some point and then add or upsert to the table
        """
        #im ont the fence about deps
        import lancedb
        from monologue.entities.AbstractEntity import BaseModel
        from monologue.core.utils.ops import pydantic_to_pyarrow_schema
        db = lancedb.connect(VECTOR_STORE_ROOT_URI)
        if isinstance(schema,BaseModel):
            schema = pydantic_to_pyarrow_schema(schema)
        return db.create_table(name=name,  schema=schema)
    
            
    def get_db_table(self):
        import lancedb
        db = lancedb.connect(VECTOR_STORE_ROOT_URI)
        return db.open_table(self._name)
                
    def upsert_records(self, records : typing.List[dict], key='id', mode='append'):
        """
        add to the table and remove anything that had the same id
        """
        if len(records):
            in_list = ",".join([f'"{r[key]}"' for r in records])
            self._dataset.delete(f"{key} IN ({in_list})")
            return lance.write_dataset(pa.Table.from_pylist(records),mode=mode,uri=self._uri)
        return self._dataset        
        
    def query_dataset(self, query):
        dataset = self._dataset
        return self._duck_client.execute(query) 
    
    def load(self, limit=None):
        """
        returns the polars data for the records
        """
        dataset = self._dataset
        limit = f"LIMIT {limit}" if limit else ""
        return self._duck_client.execute(f"SELECT * FROM dataset {limit}") 