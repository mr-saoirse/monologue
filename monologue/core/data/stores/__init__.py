from .AbstractStore import AbstractStore
from .ColumnarStore import ColumnarDataStore
from .VectorStore import VectorDataStore
from .EntityStore import EntityDataStore
import typing
from monologue.entities import AbstractEntity


def tools_for_entity(entity: AbstractEntity) -> typing.List[AbstractStore]:
    """
    In general we would load these form some database but this is good for quick testing

    We need some good quality data for all stores to be used for the same entity
    because they need to be rich statistics, textual and strong entity keys
    """
    return [
        ColumnarDataStore(entity=entity),
        VectorDataStore(entity=entity),
        EntityDataStore(entity=entity),
    ]


from .VectorStore import VECTOR_STORE_ROOT_URI
from .ColumnarStore import COLUMN_STORE_ROOT_URI
