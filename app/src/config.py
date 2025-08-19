import logging
import logging.config
import os

def get_logger(name: str):
    """
    Set up logging configuration from a file and return a logger instance.
    """
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logging_config.ini')
    if os.path.exists(config_file):
        logging.config.fileConfig(config_file)
    else:
        logging.basicConfig(level=logging.INFO)
        logging.warning(f"logging_config.ini not found at {config_file}. Using basic config.")
    return logging.getLogger(name)