"""
Entity store is key -> type -> value store
Normally there is one type but there could be many
"""
from langchain.agents import Tool
from typing import Any, List
from monologue.core.data.clients import TypedKeyRegistry
from monologue.entities import AbstractEntity
from monologue import logger
from monologue.core.data.stores import AbstractStore


class EntityDataStore(AbstractStore):
    def __init__(self, entity: AbstractEntity, extra_context=None):
        super().__init__(entity=entity)
        self._db = TypedKeyRegistry(
            schema=self._entity_namespace, type_key=self._entity_name
        )
        self._tool = self.as_tool()

    @property
    def entity_name(self):
        return self._entity_name

    def __getitem__(self, key):
        return self._db[key]

    def __setitem__(self, key, value):
        self._db[key] = value

    def insert_row(self, d, **options):
        key = d[self._key_field]
        self._db[key] = d
        return d

    def upsert_row(self, d, **options):
        key = d[self._key_field]
        self._db.merge_dict(key, d)
        return d

    def add(self, records: List[AbstractEntity]):
        assert (
            self._entity_name
        ), "You cannot use the add function without specifying the entity name and namespace in the constructor"
        records = [r.dict() for r in records]
        records = [r for r in records if len(r)]
        logger.info("Populating entities")
        for record in records:
            self.insert_row(record)

    def __getitem__(self, key):
        value = self._db[key]
        return value

    def __call__(self, question):
        return self._tool.run(question)

    def as_tool(self):
        """

        note we always provide a help hint pointer to another tool
        """

        help_text = (
            f"use the stats tool for entities of type {self._entity_name} to answer questions of a statistical nature or the further details tool for entities of type {self._entity_name} for more arbitrary questions",
        )

        def fetcher(keys):
            keys = keys.split(",")
            # do some key cleansing
            # TODO figure out what the regex is to do this safely for identifiers - this is a crude way as we experience cases
            # Tests for new lines and quotes etc in the thing or stuff at the ends that is not simple chars
            keys = [
                k.rstrip("\n").lstrip().rstrip().strip('"').strip("'") for k in keys
            ]
            # the store may internal try and add something to the map
            # for example if we pass in A B C D it may lookup A B C and add D in the result but map context from ABC
            d = {k: self._db[k] for k in keys}
            d["help"] = help_text
            return d

        return Tool(
            name="Entity Resolution Tool",
            func=fetcher,
            description=f"""use this tool when you need to lookup entity attributes relating to {self._entity_name} or find out more about some code or identifier.
                Do not use this tool to answer questions of a statistical nature.
                You should pass a comma separated list of known or suspected entities to use this tool""",
        )
