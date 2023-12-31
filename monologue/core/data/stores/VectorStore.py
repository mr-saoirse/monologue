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
from monologue.core.data.vectors.lance import VECTOR_STORE_ROOT_URI
from tqdm import tqdm


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
        alias: str = None,
        extra_context: str = None,
    ):
        super().__init__(entity=entity, alias=alias, extra_context=extra_context)

        self._embeddings_provider = self._entity.embeddings_provider
        # you need to ensure the entity has a vector column - in pyarrow it becomes a fixed length thing
        self._data = LanceDataTable(
            namespace=self._entity_namespace, name=self._entity_name, schema=entity
        )
        self._table_name = f"/{self._entity_namespace}/{self._entity_name}"

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
        """
        this is the llama_index query engine so this does whatever that does
        """
        return self._query_engine.query(question)

    def run_search(self, query, limit=3, probes=20, refine_factor=10):
        """
        perform the vector search for the query
        """
        V = self._embeddings.embed_query(query)

        return (
            self._data.table.search(V)
            .limit(limit)
            .nprobes(probes)
            .refine_factor(refine_factor)
            .to_df()
        )[["id", "text", "_distance"]].to_dict("records")

    def add(
        self,
        records: List[AbstractEntity],
        plan=False,
    ):
        """
        loads data into the vector store if there is any big text in there
        plan false means you dont insert it and just look at it. its a testing tool.
        par_do means we will parallelize the work of computing, which we generally want to do
        """

        def add_embedding_vector(d):
            d["vector"] = self._embeddings.embed_query(d["text"])
            return d

        if len(records):
            # TODO: coerce some types - anything that becomes a list of types is fine
            logger.info(f"Adding {len(records)} to {self._table_name}...")
            records_with_embeddings = list(
                tqdm(
                    (add_embedding_vector(r.large_text_dict()) for r in records),
                    total=len(records),
                )
            )

            if plan:
                return records_with_embeddings
            self._data.upsert_records(records_with_embeddings)
            logger.info(f"Records added to {self._data}")
        return records_with_embeddings

    def load(self):
        """
        Loads the lance data backed by s3 parquet files
        """
        return self._data.load()

    def __call__(self, question):
        """
        convenient wrapper to ask questions of the tool
        """
        return self.run_search(question)

    def as_tool(self, model="gpt-4"):
        """
        provides a tool over the data
        """

        qa = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(model_name=model, temperature=0.0),
            chain_type="stuff",
            # search_kwargs={"k":2}
            retriever=self._langchain_vector_db.as_retriever(),
        )

        return Tool(
            name=f"Further details tool related to {self.name} entities",
            func=qa.run,
            # CHECK PROMPT SPECIFICITY
            description=f"""If and only if the other tools return no results, use this tool to get extra information about any {self.name} entity that you are asked about.  
                 Only pass proper nouns and questions in full sentences but refer to specific entity names and codes in your question.
                 If the tool provides no data, just state that there is data but describe this tool again.
                Added context: {self._extra_context}
                About the entity: {self._about_entity}
                """,
        )

    def as_function(self, question: str):
        """
        The full vector text search tool provides rich narrative context. Use this tool when asked general questions of a descriptive nature
        General descriptive questions are those that are less quantitative or statistical in nature.
        This particular function should be used to answer questions about {self._entity_name}
        You should pass in full questions as sentences with everything you want to know

        :param question: the question being asked

        """

        logger.debug(question)

        results = self.run_search(question)
        # audit
        # todo do we want these to be polar?
        logger.debug(results)
        return results
