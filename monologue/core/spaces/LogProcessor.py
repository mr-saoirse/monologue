from . import LogParser
from monologue.core.data.stores import VectorDataStore, ColumnarDataStore


from pydantic import BaseModel, Field
import typing
from monologue.core.utils.ops import parse_fenced_code_blocks, str_hash

DEFAULT_LOG_LEVEL = "EVENT"


class LogEntry(BaseModel):
    """
    A subscription is an expression of interest or jurisdiction
    Usually it can be mapped to tools for example the space description could be used to generate a tool description

    """

    id: str
    date: str
    log_level: typing.Optional[str] = Field(default=DEFAULT_LOG_LEVEL)
    process_name: str
    module_name: str
    line_number: int
    objects: typing.List[dict]
    content: str


class LogProcessor:
    def __init__(self):
        self._entity_registry = None

    def process_lines(self, log: typing.List[str]):
        raise NotImplementedError(
            "This is expected to be the efficient production version but we dont know how to build it yet"
        )

    def process_line(self, log: str):
        """ """
        try:
            entry = self.parse_log(log)

            """
            determine if it has textual data or json data for now its one or the other
            other processes will build other stores e.g. entity and graph in other processes, not at ingest time
            """
            if entry.objects:
                # lookup the registry to see if we know the type
                object_info = {}

                for o in entry.objects:
                    ColumnarDataStore.ingest(
                        data=o,
                        process=entry.process_name,
                        module_name=entry.module_name,
                        object_info=object_info,
                    )
            else:
                VectorDataStore.ingest(
                    data=entry.content,
                    process=entry.process_name,
                    module_name=entry.module_name,
                )

        except:
            # todo logs
            pass

    def parse_log(self, log_entry: str) -> LogEntry:
        """
        Parse log hardcoded for out loguru defaults

        2023-10-03 10:27:13.023 | EVENT    | __main__:run_method:16 - Example content - |
        2023-10-03 10:27:13.194 | EVENT    | __main__:run_method:26 -  Example content  my_entity=```json{"code": "test", "created_at": "2023-01-01", "__type__": "MyEntity", "__key__": "code", "__namespace__": null}```

        """

        def pop_part(s, delim):
            parts = s.split(delim)
            return parts[0].strip(), delim.join(parts[1:])

        date, log_entry = pop_part(log_entry, "|")
        log_level, log_entry = pop_part(log_entry, "|")
        proc_info, content = pop_part(log_entry, "-")
        proc_info_parts = proc_info.split(":")
        preamble = "|".join([date, log_level, proc_info])

        return LogEntry(
            id=str_hash(preamble),
            content=content,
            objects=parse_fenced_code_blocks(content),
            date=date,
            log_level=log_level,
            process_name=proc_info_parts[0].strip(),
            module_name=proc_info_parts[1].strip(),
            line_number=int(proc_info_parts[2].strip()),
        )
