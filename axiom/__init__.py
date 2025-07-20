import logging
import coloredlogs

logger: logging.Logger = logging.getLogger(__name__)

coloredlogs.install(
    level="INFO",
    logger=logger,
    fmt="%(asctime)s %(name)-4s %(levelname)-4s %(message)s",
)
