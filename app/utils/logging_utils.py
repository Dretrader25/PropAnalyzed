import logging
import sys

def setup_logging(level: int = logging.INFO) -> None:
    """
    Configures basic logging for the application.
    Outputs to stdout.
    """
    # Get the root logger
    root_logger = logging.getLogger()

    # Remove any existing handlers to avoid duplicate logs if this is called multiple times
    # or if Uvicorn/FastAPI adds its own. Be careful with this in complex setups.
    # For now, this is simple. If Uvicorn has its own good defaults, we might not need this.
    # However, explicit setup gives more control.
    if root_logger.hasHandlers():
        for handler in root_logger.handlers[:]: # Iterate over a copy
             root_logger.removeHandler(handler)
             handler.close() # Close the handler properly

    # Add a new stream handler
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # You can also set levels for specific loggers, e.g.:
    # logging.getLogger("httpx").setLevel(logging.WARNING)
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level {logging.getLevelName(level)}.")
