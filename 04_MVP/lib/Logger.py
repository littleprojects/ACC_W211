

import os
import logging
from logging.handlers import RotatingFileHandler


def parse_log_level(log_level_str) -> int:
    """
    Map a string to a logging level.
    Defaults to INFO if unknown.
    """

    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    # UPPER case for to compare or INFO as fallback
    return log_levels.get(str(log_level_str.upper()), logging.INFO)


class Log:
    """
    Wrapper-Classe for a Logger with output- und Rotating-File-Handler.
    """

    def __init__(self, name: str, level: int = logging.INFO, log_dir: str = "log", config = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.name = name

        # Verhindern, dass Handler mehrfach hinzugefügt werden
        if not self.logger.handlers:
            formatter = self._get_formatter()

            # Console Handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # File Handler
            if log_dir is not None:
                log_file = os.path.join(log_dir, f"Log_{name}.txt")
                # NOTE: Logfile name is hardcoded now because all submodule have there own names -> creats lot log files -> this fix will create it in one
                #log_file = os.path.join(log_dir, f"Log_MVP.txt") # but now they cant write at one logfile :(
                os.makedirs(os.path.dirname(log_file), exist_ok=True)

                file_handler = RotatingFileHandler(
                    log_file, maxBytes=1 * 1024 * 1024, backupCount=2, encoding="utf-8"
                )
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)

                # set loglevel form config
        if config is not None:
            if hasattr(config, 'loglevel'):
                self.logger.setLevel(parse_log_level(config.loglevel))

                self.logger.debug('Set loglevel: ' + config.loglevel)

    def _get_formatter(self) -> logging.Formatter:
        """Erzeugt ein einheitliches Format für alle Handler."""
        return logging.Formatter(
            fmt="%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S" # .%f (microsec)
        )

    def get_logger(self) -> logging.Logger:
        """Gibt den konfigurierten Logger zurück."""
        return self.logger
