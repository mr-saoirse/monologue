from typing import Union, List, Optional
from pydantic import Field, BaseModel, create_model, BaseConfig
import json
import numpy as np

# When we are mature we would store configuration look this somewhere more central
INSTRUCT_EMBEDDING_VECTOR_LENGTH = 768
OPEN_AI_EMBEDDING_VECTOR_LENGTH = 1536


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        dtypes = (np.datetime64, np.complexfloating)
        if isinstance(obj, dtypes):
            return str(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            if any([np.issubdtype(obj.dtype, i) for i in dtypes]):
                return obj.astype(str).tolist()
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


class AbstractEntity(BaseModel):
    @classmethod
    @property
    def namespace(cls):
        """
        Takes the namespace from config or module - returns default if nothing else e.g. dynamic modules
        """
        if hasattr(cls, "Config"):
            if hasattr(cls.Config, "namespace"):
                return cls.Config.namespace

        # TODO: simple convention for now - we can introduce other stuff including config
        parts = cls.__module__.split(".")
        return parts[-2] if len(parts) > 2 else "default"

    @classmethod
    @property
    def entity_name(cls):
        # TODO: we will want to fully qualify these names
        s = cls.schema()
        return s["title"]

    @classmethod
    @property
    def full_entity_name(cls, sep="_"):
        return f"{cls.get_namespace()}{sep}{cls.get_entity_name()}"

    @classmethod
    @property
    def key_field(cls):
        s = cls.schema()
        key_props = [k for k, v in s["properties"].items() if v.get("is_key")]
        # TODO: assume one key for now
        if len(key_props):
            return key_props[0]

    @classmethod
    @property
    def fields(cls):
        s = cls.schema()
        key_props = [k for k, v in s["properties"].items()]
        return key_props

    @classmethod
    @property
    def about_text(cls):
        if hasattr(cls, "config"):
            c = cls.config
            return getattr(c, "about", "")

    @classmethod
    @property
    def embeddings_provider(cls):
        if hasattr(cls, "Config"):
            if hasattr(cls.Config, "embeddings_provider"):
                return cls.Config.embeddings_provider

    def large_text_dict(cls):
        return cls.dict()

    def __repr__(cls):
        """
        For the purposes of testing some logging with types
        the idea of using markdown and fenced objects is explored
        """

        d = cls.dict()
        d["__type__"] = cls.get_entity_name()
        d["__key__"] = cls.get_key_field()
        d["__namespace__"] = cls.get_namespace()
        d = json.dumps(d, cls=NpEncoder, default=str)
        return f"""```json{d}```"""

    @classmethod
    def create_model(cls, name, namespace=None, **fields):
        """
        For dynamic creation of models for the type systems
        create something that inherits from the class and add any extra fields
        """

        return create_model(name, **fields, __module__=namespace, __base__=cls)


class AbstractVectorStoreEntry(AbstractEntity):
    name: str = Field(is_key=True)
    text: str = Field(long_text=True)
    doc_id: Optional[str]
    vector: Optional[List[float]] = Field(
        embedding_vector_length=OPEN_AI_EMBEDDING_VECTOR_LENGTH
    )
    id: Optional[str]
