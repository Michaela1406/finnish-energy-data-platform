import logging
from unicodedata import name

def get_logger(name: str) -> logging.Logger:
    """Create and configure a project logger."""
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.setLevel(logging.INFO)

    return logger