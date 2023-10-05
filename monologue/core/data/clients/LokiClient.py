"""

The most basic LokiClient imaginable
Its job is to watch pods in a specific endpoint and parse out the log levels we care about
The result should be a steady stream of messages with exactly the same format
We do not do much error handling at this stage as this is just a PoC to fire and forget messages

these messages are picked up by our log parser which sends stuff to stores. 
We just keep an agent run continuously doing this without any attempt to distribute processing etc.


log lines such as are returned ??
s = 'level=info ts=2023-10-05T01:41:52.558304323Z caller=filetargetmanager.go:181 msg="received file watcher event" name=/var/log/pods/argo_workflow-controller-f58c79-wlvkx_07fd4192-7cc6-4322-9e96-6cb78b84b1fb/workflow-controller/3.log op=CREATE'

"""
import os
import requests
from pydantic import BaseModel
import typing
import re

#
LOKI_ADDR = os.environ.get("LOKI_ADDR", "http://localhost:3100")


class LogEntry(BaseModel):
    level: str
    ts: str
    caller: str
    msg: str
    name: typing.Optional[str]
    op: typing.Optional[str]


class LogInfo(BaseModel):
    app: str
    container: str
    filename: str
    instance: str
    job: str
    namespace: str
    node_name: str
    pod: str
    stream: str
    values: typing.List[LogEntry]


class LokiClient:
    """
    The Loki will read logs - on k8s when running make sure to set the env var

    c = LokiClient()
    print(c.labels)

    #we can parse the logs if try_parse is set
    #its always best to do that if we are sure of the interface but we can disable to see what is coming back
    #you need to pass in valid logQl queries as the query parameter
    #TODO understand how to filter and query to tail the logs of interest
    result = c.query('{app="promtail"}',try_parse=True)
    result[0].values

    """

    def __init__(self):
        self._root = f"{LOKI_ADDR}/loki/api/v1"

    @staticmethod
    def parse_log_string(s):
        pattern = r'(\w+)="(.*?)"|(\w+)=([^\s]+)'
        matches = re.findall(pattern, s)
        key_value_pairs = {}
        for match in matches:
            # Use the first non-empty group as the key and the second as the value
            key = match[0] if match[0] else match[2]
            value = match[1] if match[1] else match[3]
            key_value_pairs[key] = value
        return key_value_pairs

    @staticmethod
    def parse_results(results):
        """
        WIP
        """

        def _parse(results):
            for r in results:
                stream = r["stream"]
                values = r["values"]
                values = [LokiClient.parse_log_string(v[1]) for v in values]
                stream["values"] = values
                yield LogInfo(**stream)

        return list(_parse(results))

    def _route(self, endpoint):
        return f"{self._root}/{endpoint}"

    def _get(self, endpoint, **query):
        uri = self._route(endpoint)
        print(uri)
        return requests.get(uri, params=query)

    @property
    def labels(self):
        response = self._get("label")
        if response.status_code == 200:
            return response.json()["data"]
        # handle
        return None

    def get_streams(self, label):
        response = self._get(f"label/{label}/values")
        if response.status_code == 200:
            return response.json()["data"]
        # handle
        return None

    def query(self, log_ql_query, limit=None, try_parse=True):
        """
        example: 'sum(rate({app="promtail"}[10m])) by (level)'
        """
        response = requests.get(self._route("query"), params={"query": log_ql_query})
        if response.status_code == 200:
            data = response.json()["data"]
            return data if not try_parse else LokiClient.parse_results(data["result"])
        # handle
        return None
