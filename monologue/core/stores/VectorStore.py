from llama_index.langchain_helpers.agents import IndexToolConfig, LlamaIndexTool
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import LanceDB
from langchain.document_loaders import DataFrameLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from monologue.entities import AbstractEntity, Union
from typing import List
import pandas as pd
from monologue.core.clients import LanceDBClient
from . import AbstractStore 
from monologue import S3BUCKET, logger

VECTOR_STORE_ROOT_URI = f"s3://{S3BUCKET}/stores/vector/v0"

class VectorDataStore(AbstractStore):
    """
    Vector store for infesting and query data
    can be used as a tool

    from res.learn.agents.data.VectorDataStore import VectorDataStore
    store = VectorDataStore(<Entity>)
    tool = store.as_tool()
    tool.run("what is your question....")

    #data = store.load()
    
    #store.add(data)

    """

    def __init__(
        self,
        entity,
    ):
        super().__init__(entity=entity)
        self._db = LanceDBClient(uri_root=VECTOR_STORE_ROOT_URI)
        self._embeddings = OpenAIEmbeddings()
        self._table_name =   f"{self._entity_namespace}_{self._entity_name}"
        
    def add(self, records: Union[List[AbstractEntity], pd.DataFrame]):
        """
        loads data into the vector store if there is any big text in there
        """
        if not isinstance(records,pd.DataFrame):
            records = [r.large_text_dict() for r in records]
            records = [r for r in records if len(r)]
            records = pd.DataFrame(records)
 
        if len(records):
            logger.info(f"Adding {len(records)} to {VECTOR_STORE_ROOT_URI}/{self._table_name}...")
            if len(records):
                self._db.ingest_text_data_store(
                    records,
                    table_name=self._table_name,
                    embeddings=self._embeddings
                )
        return records

    def load(self) -> pd.DataFrame:
        """
        Loads the lance data backed by s3 parquet files         
        """
        return self._db.load(self._table_name).to_pandas()

    def as_tool(self, text_column='text', model='gpt-4', debug_db=False):
        """
        provides a tool over the data
        hard coding text field for now
        """
        table, df = self._db.ingest_text_data_store(
            None, table_name=self._table_name, embeddings=self._embeddings, text_column=text_column
        )
        loader = DataFrameLoader(df, page_content_column=text_column)
        documents = RecursiveCharacterTextSplitter(chunk_size=1000).split_documents(loader.load())
        docsearch = LanceDB.from_documents(documents, self._embeddings, connection=table)
        
        if debug_db:
            return docsearch
        
        qa = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(model_name=model, temperature=0.0),
            chain_type="stuff",
            retriever=docsearch.as_retriever(),
        )

        return Tool(
            name=f"Further details tool relate to {self._entity_name} entities",
            func=qa.run,
            description=f"""If and only if the other tools return no results, use this tool to get extra information about any {self._entity_name} entity that you are asked about.  
                Do not pass identifiers and codes to this tool. Only pass proper nouns and questions in full sentences.
                Added context: {self._extra_context}
                About the entity: {self._about_entity}
                """,
        )
    


# def tool_from_index(
#     index,
#     name="Vector Index",
#     description="useful for when you want to answer queries about ONE platform",
# ):
#     """
#     Simple wrapper example around an index like a slack index to build a tool with some hard coded settings for now
#     """
#     tool_config = IndexToolConfig(
#         index=index,
#         name=name,
#         description=description,
#         index_query_kwargs={"similarity_top_k": 3},
#         tool_kwargs={"return_direct": True},
#     )

#     tool = LlamaIndexTool.from_tool_config(tool_config)
#     return tool
 