# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light,md
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

import sys
sys.path.append("../")

import monologue
#we use this to get fenced stuff out
from monologue.core.utils.ops import parse_fenced_code_blocks
#saves typing, fairly basic- generate pydantic types from example data
from monologue.core.utils.ops import pydantic_type_generator
#the entities we will create extend this which does the repr and pulls out some metadata
from monologue.entities import AbstractEntity


# ## Illustrate the type representation in logs

# +
from pydantic import Field
class MyEntity(AbstractEntity):
    code: str = Field(is_key=True)
    created_at: str

my_entity = MyEntity(code='test', created_at= "2023-01-01")
my_entity
# -

# ## Show how the Columnar Store works

from monologue.core.data.stores import ColumnarDataStore
from monologue.entities.examples import NycTripEvent
store = ColumnarDataStore(NycTripEvent)
store

# ### how we add data to the store

# +
# import pandas as pd
# data = pd.read_csv("/Users/sirsh/Downloads/nyc_trip_data_sample.csv") 
# store.add(data)
# -

# ### load the tool and ask questions

tool = store.as_tool()
tool

tool.run("What is least popular destination in new york city? Who has travelled there?")

# # Vector Store Loading

# ### bios

import pandas as pd
from monologue.core.data.stores import VectorDataStore
from monologue.core.utils.ops import pydantic_to_pyarrow_schema
from monologue.entities.examples import *

# +
data = pd.read_csv("/Users/sirsh/Downloads/marvel_bios.csv").rename(columns={'entity_key':'id'})
data['id'] = data['id'].map(lambda x: x.replace('"',''))
data['name'] = data['id'].map(lambda x: x.split('_')[0])

data['doc_id'] = data['name']
data.tail()
# -

store = VectorDataStore(AvengingPassengersInstruct)
data = [AvengingPassengersInstruct(**d) for d in data.to_dict('records')]
#result = store.add(data)

store.load()

store("Who is Hank Pym?")

store("What can you tell me about captain america? What was his real name?")

# ### places

data = pd.read_csv("/Users/sirsh/Downloads/nyc_zones.csv").drop(columns='id',index=1).rename(columns={'entity_key':'id'})
data['doc_id'] = data['id']
data['name'] = data['id']
data.head()

records = [Places(**d) for d in data.to_dict('records')]
#store.add(data)

store = VectorDataStore(Places)
#e = store.add(records[:10],plan=False)

store.load()

store("What can you tell me about civil airport in East Elmhurst Queens?")

store.query_index("What can you tell me about civil airport in East Elmhurst Queens?")




