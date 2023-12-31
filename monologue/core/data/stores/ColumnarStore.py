from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from monologue.entities import AbstractEntity, List, Union
from monologue import S3BUCKET
from monologue.core.data.clients import DuckDBClient
import pandas as pd
from . import AbstractStore
from monologue import logger
from monologue.core.data.io import merge, read, get_query_context, write

COLUMN_STORE_ROOT_URI = f"s3://{S3BUCKET}/stores/columnar/v0"


class ColumnarDataStore(AbstractStore):
    """
    Load a datastore or use it as a too

    store = ColumnarDataStore(NycTripEvent)
    #populate with some sample data e.g.
    #data = pd.read_csv("/Users/sirsh/Downloads/nyc_trip_data_sample.csv")
    #we need to send lists of dicts or Polar
    #d = store.add(data.to_dict('records'))
    #illustrate fetching some in the schema
    data = store.fetch_entities()
    #ask questions of the store
    store("Who traveled most often to JFK Airport")


    """

    def __init__(self, entity: AbstractEntity, extra_context=None):
        super().__init__(entity=entity)
        self._entity = entity
        self._db = DuckDBClient()
        self._table_path = f"{COLUMN_STORE_ROOT_URI}/{self._entity_namespace}/{self._entity_name}/parts/0/data.parquet"
        # base class

        self._extra_context = extra_context

    def load(self):
        return read(self._table_path)

    def __call__(self, question):
        return self.run_search(question)

    def __repr__(self) -> str:
        return f"ColumnarDataStore({self._table_path})"

    @property
    def query_context(self):
        return get_query_context(self._table_path, name=self._entity_name)

    def query(self, query):
        ctx = self.query_context
        return ctx.execute(query).collect()

    def fetch_entities(self, limit=10) -> List[AbstractEntity]:
        data = self.query(f"SELECT * FROM {self._entity_name} LIMIT {limit}").to_dicts()
        return [self._entity(**d) for d in data]

    def add(self, records: List[AbstractEntity], mode="merge"):
        """
        Add the fields configured on the Pydantic type that are columnar - defaults all
        These are merged into parquet files on some path in the case of this tool
        """

        if len(records):
            logger.info(f"Writing {self._table_path}. {len(records)} records.")
            if mode == "merge":
                logger.info(f" Merge will be on key[{self._key_field}]")
            return (
                merge(self._table_path, records, key=self._key_field)
                if mode != "overwrite"
                else write(self._table_path, records)
            )
        return records

    def run_search(
        self,
        question,
        return_type="dict",
        build_enums=True,
        limit_table_rows=200,
        llm_model="gpt-4",
    ):
        def parse_out_sql_and_try_clean(s):
            if "```" in s:
                s = s.split("```")[1].replace("sql", "").strip("\n")
            return s.replace("CURRENT_DATE ", "CURRENT_DATE()")

        llm = ChatOpenAI(model_name=llm_model, temperature=0.0)

        enums = {} if not build_enums else self._db.inspect_enums(self._table_path)

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
        # TODO better LLM and Duck exception handling
        except Exception as ex:
            return []

    def as_tool(
        self,
    ):
        """
        Create a tool for answering questions about the entity
        """

        return Tool(
            name=f"Stats and data table tool relating to {self._entity_namespace} {self._entity_name}",
            func=self.run_search,
            description=f"""Use this tool to answer questions about aggregates or statistics or to get sample values or lists of values relating to {self._entity_namespace} {self._entity_namespace}. 
            Do not select any values that are not in the provided list of columns. 
            Provide full sentence questions to this tool. If 0 results are returned, do not trust this tool completely.
            Added context: {self._extra_context}
            About the entity: {self._about_entity}
            """,
        )

    def as_function(self, question: str):
        """
        The full columnar data tool provides statistical and quantitative results but also key attributes. Usually can be used to answer questions such as how much, rank, count etc. and random facts about the entity.
        this particular function should be used to answer questions about {self._entity_name}

        :param question: the question being asked
        """

        results = self.run_search(question)
        # audit
        logger.debug(results)
        return results
