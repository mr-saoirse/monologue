from loguru import logger
import os
from functools import partial


ai_level = logger.level("EVENT", no=27, color="<yellow>", icon="🤖")

log_event = partial(logger.log, "EVENT")

S3BUCKET = os.environ.get(f"MONO_BUCKET", "")
