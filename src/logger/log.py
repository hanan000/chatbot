import os

from loguru import logger

from helpers.dir_helper import DirectoryHelper


class LOG:
    lvl = "DEBUG"

    """Configure the logger to write logs to the specified file.

    Attributes:
        rotation (str): Controls log file rotation based on either file size or time.
            - When specified as a time interval, log rotation will occur at regular intervals.
              For example, "1 day" creates a new log file every day.
            - When specified as a file size, log rotation will occur when the current log file
              reaches the specified size. For example, "10 MB" creates a new log file when
              the log file size reaches 10 megabytes.
        retention (str): Sets the retention policy for log files, determining how long log files are kept.
            - When specified as a time duration, log files older than the specified duration are subject
              to deletion or archival. For example, "7 days" retains log files for 7 days.
        level (str): The minimum log level at which messages will be recorded. Messages with levels
            less severe than this will be ignored. Common levels include DEBUG, INFO, WARNING, ERROR, and CRITICAL.


    Usage:
        >>> LOG.debug('My message: %s', debug_str)
        13:12:43.673| DEBUG - :<module>:1 - DEBUG - My message: hi
        >>> LOG('custom_name').debug('Another message')
        13:13:10.462| DEBUG  logger.log:info:no.- custom_name - DEBUG - Another message
    """

    # Configure the logger to write logs to the specified file
    # logger.remove()  # Remove any previously added sinks
    if os.environ.get("PROJECT_ENV") != "prod":
        logger.add(
            DirectoryHelper.LOGS_DIR + "/logs.log", rotation="100 MB", retention="356 days", level=lvl
        )
    _custom_name = None

    def __init__(self, name):
        LOG._custom_name = name

    @classmethod
    def error(cls, message):
        logger.error(message)

    @classmethod
    def warning(cls, message):
        logger.warning(message)

    @classmethod
    def info(cls, message):
        logger.info(message)

    @classmethod
    def debug(cls, message):
        logger.debug(message)

    @classmethod
    def exception(cls, message):
        logger.exception(message)


# Usage:


if __name__ == "__main__":
    LOG.error("This is an error message.")
    LOG.warning("This is a warning message.")
    LOG.info("This is an info message.")
    LOG.debug("This is a debug message.")

    try:
        1 / 0  # Trigger a ZeroDivisionError
    except Exception as e:
        LOG.exception("An exception occurred: {}".format(e))
        LOG.debug("This is a debug message.")
