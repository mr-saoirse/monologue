from monologue.core.data.clients import KeyRegistry
from monologue.core.data.stores import VECTOR_STORE_ROOT_URI, COLUMN_STORE_ROOT_URI
from monologue.core.data.io import ls
from . import SpaceSubscription


class IndexManager(KeyRegistry):
    """
    The index manager manages subscriptions
    subscriptions are a queryable set of spaces that can be managed
    - We store some keys in memory (explore configure subsets of fields for entity store)
    - We store subscriptions in LanceDB so we can do text search on them
    - We check the audit trail to make exchanges between spaces, locking files etc

    """

    def __init__(self):
        pass

    def dump(self):
        """
        dumps the subscription to the column store
        """
        pass

    def _verify_sync(self):
        """
        read from the stores/and make sure all entities are known
        """
        pass

    def delete_store(self, mode, namespace, entity):
        """
        remove the physical store and remove the index or mark it as deleted rather (date)
        """
        pass

    def list_physical_stores(self):
        """
        using our path convention, find all the stores, namespaces and names
        """
        manifests = ls(COLUMN_STORE_ROOT_URI) + ls(VECTOR_STORE_ROOT_URI)

        def t(s):
            parts = s.split("/")
            if len(parts) > 7:
                return (parts[4], parts[6], parts[7])

        tuples = set([t(f) for f in manifests if t(f)])

        return [{"mode": t[0], "namespace": t[1], "name": t[2]} for t in tuples]

    @staticmethod
    def suggest_initial_tools(context):
        return None


"""
Advanced
- manage schema migrations
- distributed/queued processing of index
"""
