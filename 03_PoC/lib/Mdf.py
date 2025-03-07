import logging
import time
from asammdf import MDF, Signal
from lib import utils


class Mdf:
    """
    Creates MDF files to Log CAN Data
    """

    def __init__(self, file_name, log, dbc=None):

        self.log = log

        self.file_name = file_name
        self.dbc = dbc

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

                    unit = ''
                    comm = ''

                    if self.dbc is not None:
                        sig = utils.dbc_signal(self.dbc, key)

                        if sig is not None:
                            if sig.unit is not None:
                                unit = sig.unit
                            if sig.comments[None] is not None:
                                comm = sig.comments[None]

                    new_siganl = {name: {'data': [],
                                             'ts': [],
                                             'unit': unit,
                                             'comment': comm
                                             }}

                    # create init dataset
                    self.data.update(new_siganl)
                    self.log.debug('add: ' + str(new_siganl))

                self.data[name]['data'].append(data)
                self.data[name]['ts'].append(ts)

            # save after X msgs
            if self.i % 1000 == 0:
                self.write_mdf()

            self.i += 1

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
                unit = self.data[name]['unit'],
                comment = self.data[name]['comment'],
                # conversion = None,
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
