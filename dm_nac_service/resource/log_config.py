import logging
from logging.config import dictConfig
from pydantic import BaseModel


class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    LOGGER_NAME: str = "dm-nac-service"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "DEBUG"

    # Logging config
    version = 1
    disable_existing_loggers = False
    formatters = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers = {
        "arthmate-lender-handoff-service": {
            "handlers": ["default"],
            "level": LOG_LEVEL,
        },
    }


dictConfig(LogConfig().dict())
logger = logging.getLogger("dm-nac-service")
logfile_handler = logging.FileHandler("dm_nac_service/logs/server.log")
logger.addHandler(logfile_handler)