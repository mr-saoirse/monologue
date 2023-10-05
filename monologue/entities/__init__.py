def load_type(namespace, entity_name):
    """
    load an entity from a module under the entities folder
    provide the qualified namespace under entities and the entity name
    """

    module = namespace
    MODULE_ROOT = "monologue.entities."
    module = module.replace(MODULE_ROOT, "")
    module = f"{MODULE_ROOT}{module}"

    return getattr(__import__(module, fromlist=[entity_name]), entity_name)


from .AbstractEntity import *

# convenient to import these here
from pydantic import Field
from typing import List, Union, Optional
