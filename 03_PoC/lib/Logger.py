
import logging
import os.path

from logging.handlers import RotatingFileHandler
#from lib.Config import Config


class Logger:
    """
    Creating logger
    """
    def __init__(self, name):
        """ Getting the logger file """
        self.logger = logging.getLogger(name)
        self.name = name

        # setup console logger
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.get_formatter())
        self.logger.addHandler(console_handler)

        log_file = os.path.join('log/Log_' + name + '.txt')

        # setup logfile
        file_handler = RotatingFileHandler(log_file, maxBytes=1 * 1024 * 1024, backupCount=1)
        file_handler.setFormatter(self.get_formatter())
        self.logger.addHandler(file_handler)

    def get_formatter(self):
        return logging.Formatter(f'%(asctime)s - {self.name} - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')

