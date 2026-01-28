import structlog
import logging
from pathlib import Path


def setup_logging(log_path: str = '/tmp/logs'):
    Path(log_path).mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
        handlers=[
            logging.FileHandler(f"{log_path}/bot.log"),
            logging.StreamHandler()
        ]
    )
    
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()


logger = setup_logging()
