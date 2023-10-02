
from loguru import logger
import os
ai_level = logger.level("EVENT", no=27, color="<yellow>", icon="🤖")


S3BUCKET = os.environ.get(f"MONO_BUCKET", "")