from monologue.core.data.stores import VectorDataStore, ColumnarDataStore
from pydantic import BaseModel, Field
import typing
from monologue.core.utils.ops import parse_fenced_code_blocks, str_hash
from monologue.entities import AbstractVectorStoreEntry, AbstractEntity
from monologue.core.utils.ops import str_hash
import re
from monologue import logger

DEFAULT_LOG_LEVEL = "EVENT"
PREAMBLE_BEGINS_REGEX = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \| .+ \|"


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
        """
        Processing line by line is EXTREMELY inefficient but its good for testing
        In principle we would need smarter batching and typing loading etc
        actually we will probably write this part in rust too
        the embeddings are a bottleneck n any case, especially for the Instruct one
        """
        try:
            entry = self.parse_log(log)

            """
            determine if it has textual data or json data for now its one or the other
            other processes will build other stores e.g. entity and graph in other processes, not at ingest time
            """
            if entry.objects:
                for o in entry.objects:
                    # the objects are parsed in the log parser to actual json objects
                    # here we load the type using embedded type info and then construct and add it
                    ptype: AbstractEntity = AbstractEntity.get_type_from_the_ossified(o)
                    ColumnarDataStore(ptype).add([ptype(**o)])
            else:
                # the t
                ptype: AbstractVectorStoreEntry = AbstractVectorStoreEntry.create_model(
                    entry.module_name, namespace="default"
                )
                # TODO - we can be more descriptive here with a more advanced interface
                #      - this is an experimental interface for testing
                name = LogProcessor.extract_content_header(entry.content, str_hash())
                obj = ptype(name=name, text=entry.content)
                VectorDataStore(ptype).add([obj])

        except Exception as ex:
            logger.debug(f"Problem parsing {log} {ex}")
            raise

    @staticmethod
    def extract_content_header(s, default=None):
        match = re.search(r"\*\*\*(.*?)\*\*\*", s)
        if match:
            return match.group(1)
        return default

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

    @staticmethod
    def log_lines_generator(log_text):
        """
        for dealing with multi line logs given a text file
        """
        log_entry = ""
        log_entry_started = False

        for line in log_text.split("\n"):
            if re.match(PREAMBLE_BEGINS_REGEX, line):
                if log_entry_started:
                    yield log_entry.strip()
                log_entry = line
                log_entry_started = True
            elif log_entry_started:
                log_entry += "\n" + line
            else:
                pass
        if log_entry_started:
            yield log_entry.strip()

    @staticmethod
    def log_lines_generator_from_generator(g):
        """
        Give another generator will consume for a match in lines
        Its like the long text one which we will probably get rid of but is handy for tests
        could refactor them to be dryer
        """
        log_entry = ""
        log_entry_started = False

        for line in g:
            print(line)
            if re.match(PREAMBLE_BEGINS_REGEX, line):
                if log_entry_started:
                    yield log_entry.strip()
                log_entry = line
                log_entry_started = True
            elif log_entry_started:
                log_entry += "\n" + line
            else:
                pass
        if log_entry_started:
            yield log_entry.strip()
