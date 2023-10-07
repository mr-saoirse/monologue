---
description: Learn about how stores can help you build agent systems
---

# Overview

Stores are how monologue ingests different types of data and make it available for querying from chat systems

```python
from monologue.core.data.stores import  ColumnarDataStore
from monologue.entities.examples import NycTripEvent
store = ColumnarDataStore(NycTripEvent)
store("What is least popular destination in new york city? Who has travelled there?")
```

