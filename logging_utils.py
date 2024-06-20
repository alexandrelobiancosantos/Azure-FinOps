import logging

def setup_logging():
    """Set up basic logging configuration."""
    logging.basicConfig(level=logging.INFO)

def handle_errors(exception, message):
    """Handle errors by logging the message and exception, then exiting the program."""
    logging.error(f"{message}: {exception}")
    exit(1)
