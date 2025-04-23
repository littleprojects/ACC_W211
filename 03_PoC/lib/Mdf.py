import logging
import time
from asammdf import MDF, Signal
from lib import utils


class Mdf:
    """
    Creates MDF files to Log CAN Data
    """

    def __init__(self, file_name, log, dbc=None, save_interval=0, logging=True):

        self.log = log

        self.file_name = file_name
        self.dbc = dbc
        # autosave interval over msg count (by time would be better)
        self.save_interval = save_interval

        self.logging = logging

        # start time of msg timestamp calc (ts_msg - ts_start)
        self.ts_start = time.time()

        # load existion file
        # self.mdf = MDF(self.file_name)

        self.data = {'signal': {'data': [], 'ts': [], 'unit': '', 'comment': ''}}

        self.i = 0

        if logging:
            self.log.info(f'MDF log to file: {file_name}')
        else:
            self.log.info('MDF logging is deactivated')

    def new_signal(self, name, unit='', comment=''):

        # add data und ts list if signal not exist
        if not (name in self.data.keys()):
            # create new signal
            new_signal = {
                name: {
                    'data': [],
                    'ts': [],
                    'unit': unit,
                    'comment': comment
                }
            }
        else:
            new_signal = {
                name: {
                    # dont change data or timestamps
                    # just update unit and comments
                    'unit': unit,
                    'comment': comment
                }
            }


        # create init dataset
        self.data.update(new_signal)
        self.log.debug('add: ' + str(new_signal))

    def add_signal(self, name, data, ts_now=None):

        if ts_now is None:
            ts_now = time.time() - self.ts_start

        ts = ts_now

        # add signal if not exist
        if not (name in self.data.keys()):

            unit = ''
            comm = ''

            # search for unit and comments
            if self.dbc is not None:
                sig = utils.dbc_signal(self.dbc, name)

                if sig is not None:
                    if sig.unit is not None:
                        unit = sig.unit
                    if sig.comments[None] is not None:
                        comm = sig.comments[None]

            self.new_signal(name, unit, comm)



        # add data only if logging is activ
        if self.logging:
            self.data[name]['data'].append(data)
            self.data[name]['ts'].append(ts)

    def add_signals(self, signals, signal_prefix=''):

        ts_now = time.time() - self.ts_start

        try:
            for key in signals.keys():

                name = signal_prefix + key
                data = signals[key]

                self.add_signal(name, data, ts_now)

            # save after X msgs
            if self.save_interval > 0:
                if self.i % self.save_interval == 0:
                    self.write_mdf()

            # increment counter
            self.i += 1

        except Exception as e:
            self.log.error('MDF: Cant add Signals ' + str(e))

    def write_mdf(self):

        # skip if logging is off
        if not self.logging:
            return False

        # create new MDF
        mdf = MDF(version='4.10')

        self.log.debug(self.data)

        for name in self.data:

            len_data = len(self.data[name]['data'])
            len_time = len(self.data[name]['ts'])

            len_list = min(len_data, len_time)

            data = list(self.data[name]['data'][0:len_list])
            ts = list(self.data[name]['ts'][0:len_list])

            self.log.debug(self.data[name])

            sig = Signal(
                data,
                timestamps=ts,
                name=name,
                #unit=self.data[name]['unit'],
                #comment=self.data[name]['comment'],
                # conversion = None,
            )

            unit = self.data[name]['unit']
            if unit is not None:
                sig.unit = unit

            comm = self.data[name]['comment']
            if comm is not None:
                sig.comment = comm

            self.log.debug(self.data[name]['unit'])
            self.log.debug(sig)

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
