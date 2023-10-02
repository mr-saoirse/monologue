from llama_index.langchain_helpers.agents import IndexToolConfig, LlamaIndexTool
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import LanceDB
from langchain.embeddings import OpenAIEmbeddings,HuggingFaceInstructEmbeddings
from langchain.chains import RetrievalQA
from monologue.entities import AbstractEntity 
from typing import List
from monologue.core.data.vectors import LanceDataSet
from . import AbstractStore 
from monologue import S3BUCKET, logger

def get_instruct_function():
    embeddings = HuggingFaceInstructEmbeddings(
        query_instruction="Represent the query for retrieval: "
    )
    
    def _f(text):
        query_result = embeddings.embed_query(text)
        return query_result

    return _f

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
        sep='_'
    ):
        super().__init__(entity=entity)
        self._full_entity_name = f"{self._entity.get_namespace(entity)}{sep}{self._entity.get_entity_name(entity)}"
        self._dataset = LanceDataSet(name=self._full_entity_name)
        #self._embeddings = OpenAIEmbeddings()
        self._embeddings = HuggingFaceInstructEmbeddings(
            query_instruction="Represent the query for retrieval: "
        )
        self._langchain_lance_db = LanceDB(self._dataset.get_db_table(), self._embeddings)
        self._table_name =   f"{self._entity_namespace}_{self._entity_name}"
         
    def add(self, records: List[AbstractEntity]):
        """
        loads data into the vector store if there is any big text in there
        """
        def add_embedding_vector(d):
            d['vector'] = self._embeddings.embed_query(d['text'])
            return d
        if len(records):
            logger.info(f"Adding {len(records)} to {self._table_name}...")
            records_with_embeddings = [add_embedding_vector(r.large_text_dict()) for r in records]
            self._dataset.upsert_records(records_with_embeddings)
        return records

    def load(self):
        """
        Loads the lance data backed by s3 parquet files         
        """
        return self._dataset.load()
    
    def __call__(self, question):
        return self.as_tool().run(question)
                

    def as_tool(self,model='gpt-4'):
        """
        provides a tool over the data
        hard coding text field for now
        """
        
        qa = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(model_name=model, temperature=0.0),
            chain_type="stuff",
            retriever=self._langchain_lance_db.as_retriever(),
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
 