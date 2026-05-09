from datetime import datetime
from settings import settings


class Logger:
    """
    Simple file-based logger with optional enable/disable switch.

    Writes timestamped log messages to a file when enabled.

    Attributes
    ----------
    enabled : bool
        Flag controlling whether logging is active.
    """

    def __init__(self):
        """
        Initialize logger.

        Logging is enabled based on application debug settings.
        """
        self.enabled = settings.debug

    def __call__(self, text):
        """
        Log a message to file.

        Parameters
        ----------
        text : str
            Message to log.

        Notes
        -----
        Message is appended to "logfile.txt" with timestamp.
        """
        if self.enabled:
            date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S : ")

            with open("logfile.txt", "a") as logfile:
                logfile.write(date_time + text + "\n")


logger = Logger()
