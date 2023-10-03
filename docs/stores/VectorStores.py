# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
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

# # Vector stores
# - the vector store uses a hance dataset to merge texual dat and embeddings (stored on s3)
# - The the store itself adds question answering and data loading interface

import sys
sys.path.append("../../")

from monologue.core.data.vectors import LanceDataSet

ds = LanceDataSet('examples_AvengingPassengersInstruct')
ds.load().head()

from warnings import filterwarnings
filterwarnings('ignore')
from monologue.entities.examples import AvengingPassengersInstruct
from monologue.core.data.stores import VectorDataStore
store = VectorDataStore(AvengingPassengersInstruct)
store

df = store.load()
df

store.query_index("Hank Pym who is he")

# +
#store("Who is hank pym of the avengers universe?")

# +
# ##reminder we can augment data from other stores
# from monologue.entities.examples import NycTripEvent
# from monologue.core.data.stores import ColumnarDataStore
# cstore = ColumnarDataStore(NycTripEvent)
# #cstore("List all the people who travelled to Carroll Gardens and their distance travelled")
# #query using polar - nice feature
# cstore.query("SELECT passenger_count, passenger_name FROM NycTripEvent limit 5")
# -



# ## Diving into Agent/Index types


