
import time
from asammdf import MDF, Signal


class Mdf:
    """
    Creates MDF files to Log CAN Data
    """

    def __int__(self, file_name, log):

        self.log = log

        self.file_name = file_name

        # starttime
        self.ts_start = time.time()

        self.mdf = MDF()
        # load existion file
        #self.mdf = MDF(self.file_name)

        #todo: create file path

    def add_signals(self, signals, signal_prefix=''):

        ts_now = time.time() - self.ts_start

        try:
            for key in signals.keys():
                name = signal_prefix + key
                data = signals[key]

                signal = Signal([data], [ts_now], name=name)
                self.mdf.append([signal])

        except Exception as e:
            self.log.error('MDF: Cant add Signals ' + str(e))

    def write_mdf(self):

        self.log.info('MDF: Write File: ' + self.file_name)
        try:
            self.mdf.save(self.file_name)
        except Exception as e:
            self.log.error('MDF: Cant write MDF File' + str(e))
