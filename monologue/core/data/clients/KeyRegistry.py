import typing
import redis
import os
from monologue.core.utils.ops import str_hash
from monologue import logger
from pickle import loads, dumps

REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
REDIS_HOST = os.environ.get("REDIS_HOST", "127.0.0.1")


class KeyRegistry:
    def __init__(self, schema="default"):
        self._schema = schema
        self._db = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)

    def _clean_keys(self, keys):
        if isinstance(str, keys):
            keys = keys.split(",")
        if isinstance(str, keys):
            keys = [keys]
        keys = [k.strip() for k in keys]
        return keys

    def get_typed_items(self, keys: typing.Union[typing.List[str], str]) -> dict:
        """Pass one or more keys and get back a map of maps

        Args:
            keys (typing.Union[typing.List[str],str]): one or more keys

        Returns:
            dict: a map of maps. Each key is a type (may be one) and the content is a dictionary
        """

        keys = self._clean_keys(keys)
        return {k: self[k] for k in keys}

    def __qualify_key(self, key):
        return f"MONOLOGUE:{self._schema}:{key}"

    def __getitem__(self, key):
        key = self.__qualify_key(key)
        data = self._db.get(key)
        return loads(data) if data else None

    def __setitem__(self, key, value):
        key = self.__qualify_key(key)
        logger.debug(f"Add: {key}:{value}")
        return self._db.set(key, dumps(value))

    def merge_dict(self, key, value):
        """ """
        _old = self[key] or {}
        _old.update(value)
        self[key] = value
        return _old

    def exists(self, key):
        key = self.__qualify_key(key)
        return self._db.exists(key)

    def register_type(self, obj: typing.Union[dict, typing.Any], name=None):
        """
        a very simplistic trick to register types so we can route stuff
        for example, pydantic named types will be registered and we can look them up.
        We could maybe add other props

        anonymous types are named based on their sorted property names - we dont care about collisions here
        """
        if not name:
            if hasattr(obj, "get_full_entity_name"):
                name = obj.get_full_entity_name()
            else:
                # these are sorted keys for dicts
                name = str_hash(sorted(list(obj)))
        id = str_hash(name)
        self[id] = {"name": name}

        return id


class TypedKeyRegistry(KeyRegistry):
    def __init__(self, schema, type_key):
        self._type_key = type_key
        super().__init__(schema=schema)

    def __qualify_key(self, key):
        return f"MONOLOGUE:{self._schema}:{self._type_key}!-!{key}"
