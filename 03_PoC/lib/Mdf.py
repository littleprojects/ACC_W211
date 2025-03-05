import logging
import time
from asammdf import MDF, Signal


class Mdf:
    """
    Creates MDF files to Log CAN Data
    """

    def __init__(self, file_name, log):

        self.log = log

        self.file_name = file_name

        # starttime
        self.ts_start = time.time()

        # load existion file
        #self.mdf = MDF(self.file_name)


        self.data = {'signal': {'data': [], 'ts': []}}

        self.i = 0

    def add_signals(self, signals, signal_prefix=''):

        ts_now = time.time() - self.ts_start

        try:
            for key in signals.keys():

                name = signal_prefix + key
                data = signals[key]
                ts = ts_now

                # add signal
                if not (name in self.data.keys()):
                    # create init dataset
                    self.data.update({name: {'data': [],
                                             'ts': [],
                                             #'unit': unit,
                                             #'comment' : ''
                                             }})
                    self.log.debug('add: ' + name)

                self.data[name]['data'].append(data)
                self.data[name]['ts'].append(ts)

            self.i += 1

            if self.i % 1000 == 0:
                self.write_mdf()

        except Exception as e:
            self.log.error('MDF: Cant add Signals ' + str(e))

    def write_mdf(self):

        # create new MDF
        mdf = MDF(version='4.10')

        for name in self.data:

            len_data = len(self.data[name]['data'])
            len_time = len(self.data[name]['ts'])

            len_list = min(len_data, len_time)

            data = list(self.data[name]['data'][0:len_list])
            ts = list(self.data[name]['ts'][0:len_list])

            sig = Signal(
                data,
                timestamps=ts,
                name=name,
                #unit = 's',
                #conversion = None,
                #comment = 'Unsigned 64 bit channel {}'
            )

            mdf.append([sig])

        #self.log.info(str(len(sigs)))
        #self.log.info(str(len(self.data)) + ' ' + str(len(self.data['CAN_0_V_ART']['data'])))
        #self.log.info(str(len(self.data)) + ' ' + str(self.data['CAN_0_V_ART']['data']))
        #self.log.info(str(len(self.data)) + ' ' + str(self.data['CAN_0_V_ART']['ts']))

        self.log.info('MDF: Write File: ' + self.file_name)
        try:
            mdf.save(self.file_name, overwrite=True, compression=True)
        except Exception as e:
            self.log.error('MDF: Cant write MDF File' + str(e))
