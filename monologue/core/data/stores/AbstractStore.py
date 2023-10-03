from monologue.entities import AbstractEntity
class AbstractStore:
    def __init__(cls, entity: AbstractEntity):
        #TODO: bit weird - want to figure out of we want to use instances or not
        cls._entity = entity
        cls._entity_name = cls._entity.get_entity_name(entity)
        cls._entity_namespace = cls._entity.get_namespace(entity)
        cls._key_field = cls._entity.get_key_field(entity)
        cls._fields = cls._entity.get_fields(entity)
        cls._about_entity = cls._entity.get_about_text(entity)
        ###############
        cls._extra_context = ""