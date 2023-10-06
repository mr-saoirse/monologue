"""
***
SPACES: how data are stored in monologue
***

1. Tables are usually named for entities and can be different store formats
2. Spaces can be views over tables or migrated tables 
3. migrated tables are copies of the data or slices of the data 

4. Entities can include process names e.g. all data from process X - typically this will be unstructured
5. Agents subscribe to spaces. They are dynamically generated from spaces and use tools defined by space subscriptions

6. Data is migrated by a delegate agent that looks at dialogues and creates valuable exchanges
- an agent will either learn to listen to another agent, ranked favorite tools
- or an agent will create a cache of data or add a subscription with a predicate dynamically (somehow)

"""

from monologue.entities import AbstractVectorStoreEntry, Field
import typing


class SpaceSubscription(AbstractVectorStoreEntry):
    """
    A subscription is an expression of interest or jurisdiction
    Usually it can be mapped to tools for example the space description could be used to generate a tool description

    subscriptions should be searchable and we build tools form them
    """

    # <space_qual>.<format>.<entity> e.g. spaces/default/vector/trips
    # space qual can be default, temporal split, or just a view hash
    id: str
    name: str
    # this is the descriptive text
    text: str
    # columnar etc
    store_type: str
    # we can inherit a space from another space by restricting it or copying data from it
    # restrictions are predicates or cache copies
    parent_space_id: typing.Optional[bool]
    perspective: str = Field(default="entity")  # enum: process | tool | view | ??? s
    primary_entity: typing.Optional[str]
    # a unique space e.g. default entity that i care about which is how i build my tools
    spaces_of_interest: typing.List[str]
    date_from: typing.Optional[str]
    date_to: typing.Optional[str]
    # other predicates
    metadata: typing.Optional[dict] = Field(default_factory={})
