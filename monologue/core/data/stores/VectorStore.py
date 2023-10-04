"""
wraps lancedb for LLM stuff.

https://gpt-index.readthedocs.io/en/latest/examples/vector_stores/LanceDBIndexDemo.html

"""

# from llama_index.langchain_helpers.agents import IndexToolConfig, LlamaIndexTool
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import LanceDB
from llama_index.indices.vector_store import VectorStoreIndex
from llama_index.vector_stores import LanceDBVectorStore
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from llama_index import ServiceContext
from llama_index.embeddings import InstructorEmbedding as LLamaIndexInstructEmbedding
from langchain.chains import RetrievalQA
from monologue.entities import AbstractEntity
from typing import List
from monologue.core.data.vectors import LanceDataTable
from monologue import logger
import warnings
from . import AbstractStore


class VectorDataStore(AbstractStore):
    """
    ***
    Vector store for infesting and query data
    can be used as an agent tool to ask questions
    ***
    Example:
        from res.learn.agents.data.VectorDataStore import VectorDataStore
        store = VectorDataStore(<Entity>)
        #tool = store.as_tool()
        store("what is your question....")
        #data = store.load()
        #store.add(data)

    """

    def __init__(
        self,
        entity: AbstractEntity,
        sep: str = "_",
        alias: str = None,
        extra_context: str = None,
    ):
        super().__init__(entity=entity, alias=alias, extra_context=extra_context)
        self._full_entity_name = (
            alias or f"{self._entity_namespace}{sep}{self._entity_name}"
        )
        self._embeddings_provider = self._entity.get_embeddings_provider(entity)
        # you need to ensure the entity has a vector column - in pyarrow it becomes a fixed length thing
        self._data = LanceDataTable(name=self._full_entity_name, schema=entity)
        self._table_name = f"{self._entity_namespace}_{self._entity_name}"

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # just two types under consideration
            logger.debug(f"Using the embedding {self._embeddings_provider}")
            if self._embeddings_provider == "instruct":
                self._embeddings = HuggingFaceInstructEmbeddings(
                    query_instruction="Represent the query for retrieval: "
                )
            else:
                self._embeddings = OpenAIEmbeddings()

            # do all this for langchain and llama_index
            self._langchain_vector_db = LanceDB(self._data.table, self._embeddings)
            vector_store = LanceDBVectorStore(
                uri=self._data.database_uri, table_name=self._data.name
            )
            # note we need to specify the embeddings - at a minimum this determines the vector length
            # if we dont do this we get cryptic errors when the query is pushed down to lance
            index = VectorStoreIndex.from_vector_store(
                vector_store, ServiceContext.from_defaults(embed_model=self._embeddings)
            )
            self._query_engine = index.as_query_engine()

    def query_index(self, question):
        return self._query_engine.query(question)

    def add(self, records: List[AbstractEntity], plan=False):
        """
        loads data into the vector store if there is any big text in there
        """

        def add_embedding_vector(d):
            d["vector"] = self._embeddings.embed_query(d["text"])
            return d

        if len(records):
            # TODO: coerce some types - anything that becomes a list of types is fine
            logger.info(f"Adding {len(records)} to {self._table_name}...")
            records_with_embeddings = [
                add_embedding_vector(r.large_text_dict()) for r in records
            ]
            if plan:
                return records_with_embeddings
            self._data.upsert_records(records_with_embeddings)
            logger.info(f"Records added")
        return records

    def load(self):
        """
        Loads the lance data backed by s3 parquet files
        """
        return self._data.load()

    def __call__(self, question):
        return self.as_tool().run(question)

    def as_tool(self, model="gpt-4"):
        """
        provides a tool over the data
        """

        qa = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(model_name=model, temperature=0.0),
            chain_type="stuff",
            retriever=self._langchain_vector_db.as_retriever(),
        )

        return Tool(
            name=f"Further details tool relate to {self.name} entities",
            func=qa.run,
            # CHECK PROMPT SPECIFICITY
            description=f"""If and only if the other tools return no results, use this tool to get extra information about any {self.name} entity that you are asked about.  
                 Only pass proper nouns and questions in full sentences but refer to specific entity names and codes in your question.
                 If the tool provides no data, just state that there is data but describe this tool again.
                Added context: {self._extra_context}
                About the entity: {self._about_entity}
                """,
        )
