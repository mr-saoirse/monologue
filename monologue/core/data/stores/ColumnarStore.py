from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from monologue.entities import AbstractEntity, List, Union
from monologue import S3BUCKET
from monologue.core.data.clients import DuckDBClient
import pandas as pd
from . import AbstractStore
from monologue import logger
from monologue.core.data.io import merge,read,get_query_context

COLUMN_STORE_ROOT_URI = f"s3://{S3BUCKET}/stores/columnar/v0"

class ColumnarDataStore(AbstractStore):
    """
    Load a datastore or use it as a too
    
    from res.learn.agents.data.ColumnarDataStore import ColumnarDataStore
    st = ColumnarDataStore(namespace='example',entity_name='order')
    data = st.load()
    st.as_tool()

    """

    def __init__(self, entity, extra_context=None):
        super().__init__(entity=entity)
        self._entity = entity
        self._db = DuckDBClient()
        self._table_path = f"{COLUMN_STORE_ROOT_URI}/{self._entity_name}/{self._entity_namespace}/parts/0/data.parquet"
        #base class
        self._extra_context = extra_context

    def load(self):
        return self._s3.read(self._table_path)
    
    def __call__(self, question):
        return self.as_tool().run(question)
    
    @property
    def query_context(self):
        return get_query_context(self._table_path, name=self._entity_name)

    def query(self, query):
        ctx = self.query_context
        return ctx.execute(query).collect()
    
    def as_tool(
        self,
        return_type="dict",
        build_enums=True,
        limit_table_rows=200,
        llm_model='gpt-4'
    ):
        """
        Create a tool for answering questions about the entity
        """

        def parse_out_sql_and_try_clean(s):
            if "```" in s:
                s = s.split("```")[1].replace("sql", "").strip("\n")
            return s.replace("CURRENT_DATE ", "CURRENT_DATE()")

        llm = ChatOpenAI(model_name=llm_model, temperature=0.0)
 
        enums = {} if not build_enums else self._db.inspect_enums(self._table_path)
        
        def ask(question):
            prompt = f"""For a table called TABLE with the {self._fields}, and the following column enum types {enums} ignore any columns asked that are not in this schema and give
                me a DuckDB dialect sql query without any explanation that answers the question below. 
                Question: {question} """
            logger.debug(prompt)
            query = llm.predict(prompt)
            query = query.replace("TABLE", f"'{self._table_path}'")
            try:
                query = parse_out_sql_and_try_clean(query)
                logger.debug(query)
                data = self._db.execute(query)
                if limit_table_rows:
                    data = data[:limit_table_rows]
                if return_type == "dict":
                    return data.to_dicts()
                return data
            #TODO better LLM and Duck exception handling
            except Exception as ex:
                return []

        return Tool(
            name=f"Stats and data table tool relating to {self._entity_namespace} {self._entity_name}",
            func=ask,
            description=f"""Use this tool to answer questions about aggregates or statistics or to get sample values or lists of values relating to {self._entity_namespace} {self._entity_namespace}. 
            Do not select any values that are not in the provided list of columns. 
            Provide full sentence questions to this tool. If 0 results are returned, do not trust this tool completely.
            Added context: {self._extra_context}
            About the entity: {self._about_entity}
            """,
        )


    def add(self, records: List[AbstractEntity]):
        """
        Add the fields configured on the Pydantic type that are columnar - defaults all
        These are merged into parquet files on some path in the case of this tool
        """
 
        if len(records):
            logger.info(f"Writing {self._table_path}. {len(records)} records. Merge will be on key[{self._key_field}]")
            return merge(self._table_path, records, key=self._key_field)
        return records
