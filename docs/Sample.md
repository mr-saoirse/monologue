---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.15.2
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

```python
import sys
import pandas as pd
sys.path.append("../")
```

```python
from monologue.core.agents import BasicToolUsingAgent,QuestionGeneratingAgent, BasicTypedResponseToolUsingAgent
from monologue.core.data.stores import VectorDataStore, ColumnarDataStore, EntityDataStore
from monologue.entities.examples import AvengingPassengersInstruct, NycTripEvent, Places, AbstractVectorStoreEntry
from monologue.core.data.stores import tools_for_entity

from monologue.core.utils.ops import pydantic_to_pyarrow_schema
pydantic_to_pyarrow_schema(Places)
```

```python
common:
  path_prefix: /tmp/loki
  storage:
    s3:
      bucketnames: bucket-name
      region: aws-region
      access_key_id: Key
      secret_access_key: Secret

storage_config:
  boltdb_shipper:
    active_index_directory: /tmp/loki/active
    shared_store: s3
    cache_location: /tmp/loki/cache
    cache_ttl: 24h

compactor:
  working_directory: /tmp/loki/compactor
  shared_store: s3
```

#### You can create dynamic types 
- this is useful because we have assumed everything is driven by types but we might not always have one

```python
tools = [VectorDataStore(AvengingPassengersInstruct, extra_context="This stores inforamtion about people travelling in New York taxis").as_tool(),
         VectorDataStore(Places, extra_context="This stores inforamtion about places in New York").as_tool(),
         ColumnarDataStore(NycTripEvent).as_tool()
        ]

agent = BasicToolUsingAgent(tools=tools, context="Answer questions about people taking trips in new york")
agent("Please provide a summary of the person who went to Carroll Gardens most often with as much detail as possible. what might they have gont to Carroll gardens?")

```

```python
import monologue
#we use this to get fenced stuff out
from monologue.core.utils.ops import parse_fenced_code_blocks
#saves typing, fairly basic- generate pydantic types from example data
from monologue.core.utils.ops import pydantic_type_generator
#the entities we will create extend this which does the repr and pulls out some metadata
from monologue.entities import AbstractEntity
```


## Illustrate the type representation in logs

```python
from pydantic import Field
class MyEntity(AbstractEntity):
    code: str = Field(is_key=True)
    created_at: str

my_entity = MyEntity(code='test', created_at= "2023-01-01")
my_entity
```

## Show how the Columnar Store works

```python
from monologue.core.data.stores import ColumnarDataStore
from monologue.entities.examples import NycTripEvent
store = ColumnarDataStore(NycTripEvent)
store
```

### load the tool and ask questions

```python
tool = store.as_tool()
tool
```

```python
tool.run("What is least popular destination in new york city? Who has travelled there?")
#or just store("ask question")
```

# Vector Store Loading


### bios

```python
import pandas as pd
from monologue.core.data.stores import VectorDataStore
from monologue.core.utils.ops import pydantic_to_pyarrow_schema
from monologue.entities.examples import *
```

```python
data = pd.read_csv("/Users/sirsh/Downloads/marvel_bios.csv").rename(columns={'entity_key':'id'})
data['id'] = data['id'].map(lambda x: x.replace('"',''))
data['name'] = data['id'].map(lambda x: x.split('_')[0])

data['doc_id'] = data['name']
data.tail()
```

```python
store = VectorDataStore(AvengingPassengersInstruct)
data = [AvengingPassengersInstruct(**d) for d in data.to_dict('records')]
#result = store.add(data)
```

```python
store.load()
```

```python
store("Who is Hank Pym?")
```

```python
store("What can you tell me about captain america? What was his real name?")
```

### places

```python
import pandas as pd
data = pd.read_csv("/Users/sirsh/Downloads/nyc_zones.csv").drop(columns='id',index=1).rename(columns={'entity_key':'id'})
data['doc_id'] = data['id']
data['name'] = data['id']
data.head()
```

```python
store = VectorDataStore(Places)
#e = store.add(records[:10],plan=False)
```

```python
records = [Places(**d) for d in data.to_dict('records')]
store.add(records)
```

```python
store.load()
```

```python
store("What can you tell me about the civil airport in East Elmhurst Queens?")
```

```python
store.query_index("What can you tell me about civil airport in East Elmhurst Queens?")
```

```python
from monologue.
```

```python

```

```python

```
