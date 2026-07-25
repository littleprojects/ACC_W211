"""
ART/DTS Class

- check inputs
- state machine
- Controller for
    - Cruise Control (VV)
    - Adaptive Cruise Control (ACC)
    - Limiter (Lim)

"""

import copy

from lib import utils

from lib.Logger import Log
from lib.Art_Data import ArtState

class ART:
    def __init__(self, config, art_data):
        
        self.config = config
        
        # Logger
        self.log = Log('ART', config=config).get_logger()

        self.art_data = art_data # ART_Data class where all information are shared
        #self.mdf = mdf

        # ART internal values
        self.art = {
            'state': ArtState.OFF,
            'last_state': 0,

            'ready': False,
            
            #'dist_factor': 100,

            #'dspl_trigger_ts': 0,
            
            # dict to remember the button states
            #'button_states': {
            #    'SFB': 0,  # Braking
            #    'WH_UP': 0,  # lever NOT ok
            #    'AUS': 0,  # lever OFF
            #    'WA': 0,  # lever ON/RESUME/+1
            #    'S_PLUS_B': 0,  # lever UP +10
            #    'S_MINUS_B': 0,  # lever DOWN -10
            #    'ART_ABW_BET': 0,  # Button Warning ON/OFF
            #    'CRASH': 0,  # Crash detection
            #    'VMAX_AKT': 0,  # Limiter
            #},
            
            
            # erros; 0 = no error
            'ready_error': 0,
        }

        # all MSG id there they need to check
        # TODO centralize this list config.filter_msg_id_can_c -> is not in ART config -> find a good way
        self.needed_msg_id_list = [
                        # mandatory msgs
                        '0x200',  # BS (Break System) - drive direction, ESP
                        '0x300',  # BS - enable ART
                        '0x236',  # ART_LRW - Steering
                        '0x238',  # ART_MRM - Buttons
                        '0x240',  # EZS - Buttons
                        '0x212',  # MS - Enable ART
                        '0x308',  # MS - Data
                        '0x312',  # MS - Moments
                        '0x412',  # Kombi - speed
                        # other msgs
                        '0x408',  # Kombi
                        '0x328',  # BS
                        '0x218',  # GS - Gearbox System
                        '0x418',  # GS
                        '0x210',  # MS (Motor System) - Pedal
                        '0x608',  # MS
                    ]

        # art can msg values dict
        self.art_msg = {}   

        # CAN C signals and messages dict
        self.vehicle_msgs = {
            'msgs': {},  # msg timestamps in [ms]
            'signals': {},  # signals as dict
        }

    def can_update(self, new_msgs):
        #self.log.info(new_msgs)

        if self.art['ready']:

            # TODO - go on

            pass

        

    def tick_10Hz(self):
        # 10 Hz tick for ART
        # - get data from ART Data
        # - check inputs
        # - state machine
        # - Controller for Cruise Control (CC), Adaptive Cruise Control (ACC), Limiter (Lim)
        # - send CAN messages

        self.log.debug("10Hz tick")

        # load data from ART Data
        self.art_msg = self.art_data.get_art_msg()
        self.vehicle_msgs = self.art_data.get_vehicle_msgs()
        
        # do the magic
        self.update_bz()    # increment message counter
        self.is_ready()     # ready check - are all messages there and in time
        # TODO

        # write data back
        self.art_data.set_art_msg(self.art_msg)
        self.art_data.set_state(self.art['state'])
        
        #self.art_data.set_vehicle_msgs(self.vehicle_msgs)

    def update_bz(self):

        BZ250h = self.art_msg['BZ250h']
       
        BZ250h += 1 # increment msg counter 

        # reset of overflow (4 bit = 0-15)
        if BZ250h > 15:
            BZ250h = 0

        # update in dict
        self.art_msg['BZ250h'] = BZ250h

        #self.log.debug('BZ: ' + str(BZ250h))

    def is_ready(self):
            """
            This function checks the CAN msgs and signals if everything is ok
            """

            # current time
            ts_now = utils.timestamp_ms()            
    
            # check all needed CAN messages (from list) received
            all_msgs_found = True
    
            for msg_id in self.needed_msg_id_list:
                if not (msg_id in self.vehicle_msgs['msgs']):
                    all_msgs_found = False
    
                    self.log.debug('Checker: ID ' + msg_id + ' not found')    
                    # stop loop
                    break
    
            # NOT all msgs found -> NOT READY
            if not all_msgs_found:
    
                if self.art['ready']:
                    self.art['ready'] = False
                    self.log.warning('Checker: Msgs incomplete')

                    # reset default output values
                    self.reset_to_default()
    
                self.art['ready_error'] = 1
                return False
    
            # no MSG ts is too old
            all_msg_in_time = True
    
            # max_delay = 500  # ms
            max_delay = int(self.config.max_msg_delay)
    
            for msg_id in self.needed_msg_id_list:
                ts_last_msg = self.vehicle_msgs['msgs'][msg_id]
    
                # delay in ms
                delay = ts_now - ts_last_msg
    
                if delay > max_delay:
                    all_msg_in_time = False
                    self.log.debug('Checker: ' + msg_id + ' is to old - ' + str(delay) + ' ms')
                    # end loop
                    break
    
            # NOT all msg in time -> NOT READY
            if not all_msg_in_time:

                if self.art['ready']:
                    self.art['ready'] = False
                    self.log.warning('Checker: Msgs to old')
                    # load default output values
                    self.reset_to_default()
    
                self.art['ready_error']  = 2
                return False
    
            # TODO: check if signals are in range
            # signals = self.vehicle_msgs['signals']
    
            # set ready values
            self.set_art_ready()
    
            self.art['ready_error'] = 0
    
            return True

    def set_art_ready(self):
        # if it was not ready before
        if not self.art['ready']:
            self.log.info('READY')

        # set
        self.art_msg['ART_OK'] = 1
        self.art_msg['TM_EIN_ART'] = 1
        self.art_msg['ART_VFBR'] = 1

        # if no chancel condition quit - we are ready to go
        self.art['ready'] = True

    def reset_to_default(self):
        # if art is not ready anymore
        # if self.art.ready is not True:

        self.log.info('RESET to default')

        # reset state
        self.art['state'] = ArtState.OFF

        target_speed = self.art_msg['V_ART'] # save target speed
        abw_akt = self.art_msg['ART_ABW_AKT'] # save ART_ABW_AKT state

        # load DEFAULT values
        self.art_msg = copy.deepcopy(self.art_data._CONST_default_values)

        self.art_msg['V_ART'] = target_speed # but remember target speed ;)
        self.art_msg['ART_ABW_AKT'] = abw_akt # remember warning config

    def status(self):

        out = ''

        if not self.art['ready']:
            out += 'NOT Ready'
        else:
            #out += f"Ready: " + str(self.art['ready'])
            out += str(self.art['state']) + " "


        return out
