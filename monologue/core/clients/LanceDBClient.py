import pandas as pd
import os
import lancedb
from monologue import S3BUCKET
from langchain.embeddings import OpenAIEmbeddings

 
class LanceDBClient:
    def __init__(self, uri_root):
        self._db = lancedb.connect(uri_root, region=os.environ.get("AWS_DEFAULT_REGION"))
         
    def load(self, table_name):
        return self._db.open_table(table_name)
    
    def ingest_text_data_store(
        self,
        df,
        table_name,
        embeddings,
        text_column="text",
        id_column="id",
        delete_existing_ids=True,
    ):
        """
        ingest data- some data merging funniness
        """
        if df is None:
            #dummy
            df = pd.DataFrame([[-1, "test"]], columns=["id", "text"])

        df = df.dropna(subset=["text"])
        text_column = "text"
        df[id_column] = df[id_column].map(str)
        try:
            table = self._db.open_table(table_name)
            df["vector"] = df[text_column].map(embeddings.embed_query)
            in_list = ",".join([f'"{_id}"' for _id in df[id_column]])
            if delete_existing_ids:
                table.delete(f"{id_column} IN ({in_list})")
            exists_fields = table.schema.names
            for f in exists_fields:
                if f not in df.columns:
                    df[f] = None
            table.add(df)
        except FileNotFoundError as fex:
            df["vector"] = df[text_column].map(embeddings.embed_query)
            table = self._db.create_table(table_name, data=df, mode="overwrite")
        return table, df
    