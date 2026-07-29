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

        self.Art_Data = art_data # ART_Data class where all information are shared
        #self.mdf = mdf

        # ART internal values
        self.art = {
            'state': ArtState.OFF,
            'last_state': 0,

            'ready': False,
            
            #'dist_factor': 100,

            #'dspl_trigger_ts': 0,
            
            # dict to remember the button states
            'button_states': {
                'SFB': 0,  # Braking
                'WH_UP': 0,  # lever NOT ok
                'AUS': 0,  # lever OFF
                'WA': 0,  # lever ON/RESUME/+1
                'S_PLUS_B': 0,  # lever UP +10
                'S_MINUS_B': 0,  # lever DOWN -10
                'ART_ABW_BET': 0,  # Button Warning ON/OFF
                'CRASH': 0,  # Crash detection
                'VMAX_AKT': 0,  # Limiter
            },            
            
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
        self.art_msg = {
            # ART_250 CAN Msg
            'DYN_UNT': 0,  # dynamic downshift suppression
            'BL_UNT': 0,  # breathtaking suppression
            'ART_BRE': 0,  # ART breaks
            'ART_OK': 0,  # ART ok
            'SLV_ART': 0,  # shift lines adaptation
            'CAS_REG': 0,  # City assist is active
            'MDYN_ART': 0,  # dynamic engine moment
            'MPAR_ART': 0,  # parity
            'ART_REG': 0,  # ART is active
            'LIM_REG': 0,  # limiter is activ
            'M_ART': 0,  # [Nm] engine moment
            'BZ250h': 0,  # msg counter 4bit = 0-15
            'MBRE_ART': 0,  # [Nm] break moment
            'GMIN_ART': 0,  # minimum gear
            'GMAX_ART': 0,  # maximum gear
            'AKT_R_ART': 0,  # shift down request from art
            
            # ART_258 CAN Msg
            'ART_ERROR': 0,  # ART error code
            'ART_INFO': 0,  # ART info light
            'ART_WT': 0,  # ART warning sound
            'S_OBJ': 0,  # standing object detected
            'ART_DSPL_EIN': 0,  # ART display on
            'V_ART': 0,  # [kph] ART set speed
            'ABST_R_OBJ': 0,  # [m] distance to relevant object
            'SOLL_ABST': 0,  # [m] distance to relevant object
            'TM_EIN_ART': 0,  # ART cruise control activ
            'ART_DSPL_BL': 0,  # blink speed control
            'ART_SEG_EIN': 0,  # show speed segments on display
            'OBJ_ERK': 0,  # object detected
            'ART_EIN': 0,  # ART on
            'ART_DSPL_LIM': 0,  # show: --- on display
            'ART_VFBR': 0,  # show: ART off
            'ART_DSPL_PGB': 0,  # show: winter tire speed reached
            'V_ZIEL': 0,  # [kph] target speed on segment display
            'ASSIST_FKT_AKT': 0,  # active function - always 0
            'AAS_LED_BL': 0,  # LED blinking
            'OBJ_AGB': 0,  # object offer adaptive cc - always 0
            'ART_ABW_AKT': 0,  # warnings are switched on NOTE: load from memory
            'ART_REAKT': 0,  # reactivation of ART after error
            'ART_UEBERSP': 0,  # ART passive
            'ART_DSPL_NEU': 0,  # show ART display again for a short time
            'ASSIST_ANZ_V2': 0,  # assist display request - always 0
            'CAS_ERR_ANZ_V2': 0,  # CAS display request - always 0
        }   

        # load art dataset
        self.art_msg = self.Art_Data.get_art_msg()

        # CAN C signals and messages dict
        self.vehicle_msgs = {
            'msgs': {},  # msg timestamps in [ms]
            'signals': {},  # signals as dict
        }

    def can_update(self, new_msgs):
        #self.log.info(new_msgs)

        # at fist the system have to be ready
        if self.art['ready']:

            # is the driver braking
            if self.is_btn_pressed(new_msgs, 'SFB', double_use=True):
                self.art_braking()

            # not braking
            if self.is_btn_pressed(new_msgs, 'SFB', mode=1):
                self.log.info('Braking End')

            # Warning ON/OFF toggle button
            if self.is_btn_pressed(new_msgs, 'ART_ABW_BET'):
                self.art_warning_button()
                # save persistent the new state
                self.Art_Data.Store.write()

            # CRASH detected
            if self.is_btn_pressed(new_msgs, 'CRASH'):
                self.log.critial('CRASH detected')
                self.reset_to_default()

            # check if lever is ok
            self.is_btn_pressed(new_msgs, 'WH_UP')

            # LEVER INPUTS
            # lever is ok
            if self.art['button_states']['WH_UP'] == 0:

                # lever OFF
                if self.is_btn_pressed(new_msgs, 'AUS'):
                    self.lever_off()

                # lever ON/RESUME/+1
                if self.is_btn_pressed(new_msgs, 'WA', mode=2):
                    self.lever_wa()

                # lever UP/+10
                if self.is_btn_pressed(new_msgs, 'S_PLUS_B', mode=2):
                    self.lever_up()

                # lever DOWN/-10
                if self.is_btn_pressed(new_msgs, 'S_MINUS_B', mode=2):
                    self.lever_down()

                # LIMITER Activation
                if self.is_btn_pressed(new_msgs, 'VMAX_AKT', double_use=True):
                    self.log.info('Limiter Mode ON')
                    # TODO self.acc_deactivation()
                    #self.art.state = ArtState.LIM

                # LIMITER deactivation
                if self.is_btn_pressed(new_msgs, 'VMAX_AKT', mode=1):  # FALLING_EDGE -> ??? don't work ->
                    self.log.info('Limiter Mode OFF')

            # TODO - signal updates for time critical updates
            # for acceleration

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
        self.art_msg = self.Art_Data.get_art_msg()
        self.vehicle_msgs = self.Art_Data.get_vehicle_msgs()
        
        # do the magic
        self.update_bz()    # increment message counter
        self.is_ready()     # ready check - are all messages there and in time
        # TODO

        # write data back
        self.Art_Data.set_art_msg(self.art_msg)
        self.Art_Data.set_state(self.art['state'])
        
        #self.Art_Data.set_vehicle_msgs(self.vehicle_msgs)

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
        self.art_msg = copy.deepcopy(self.Art_Data._CONST_default_values)

        self.art_msg['V_ART'] = target_speed # but remember target speed ;)
        self.art_msg['ART_ABW_AKT'] = abw_akt # remember warning config

    def is_btn_pressed(self, data, signal, mode=0, double_use=False):
        """
        data is a dict {'signal_name':0, ...}

        Modes
        0 = Rising Edge - button is now pressed - DEFAULT
        1 = Falling Edge - button is not pressed anymore
        2 = Holding - Triggers output every x time during long hold
        Modes not needed now:
        falling edge, is ON, is OFF

        double_use - if the same button is used more times
        for example for Mode 0 and 1, set the first button check on double_use=True
        NOTE: the last button check have to be double_use=False - it set the last state to compare to the new one
        """
        
        out = False

        # signal_key is in data
        if signal in data:
            # get signal value
            signal_value = data[signal]

            # MODE 0: RISING EDGE DETECTION
            if mode == 0 or mode == 2:
                # is button pressed?
                if signal_value == 1:
                    # YES it is pressed now
                    # but was it pressed before?
                    if self.art['button_states'][signal] == 0:
                        # YES it was not pressed before -> RISING EDGE detected -> action
                        self.log.debug('Button: ' + signal + ' - Rising Edge detection')
                        out = True               

            # MODE 1: Falling Edge - button is not pressed anymore
            if mode == 1:
                # is button NOT pressed now?
                if signal_value == 0:
                #if signal_value == 0 and self.art['button_states'][signal] > 0:
                    # YES it is NOT pressed now
                    # but was it pressed before?
                    # if self.art['button_states'][signal] == 1:
                    if self.art['button_states'][signal] > 0:  # adaption to handle timestamps in button states
                        # YES it was pressed before -> FALLING EDGE detected -> action
                        self.log.debug('Button: ' + signal + ' - Falling Edge detection')
                        out = True

            # MODE 2: Holding - Triggers output every x time during long hold
            if mode == 2:
                # is button pressed now
                if signal_value == 1:
                    now = utils.timestamp_ms()

                    hold_time = 0

                    if self.art['button_states'][signal] > 1:
                        # how long is button already pressed
                        hold_time = now - self.art['button_states'][signal]

                    # is it over the holding time
                    if hold_time >= self.config.lever_hold_time:
                        # reset trigger holding time
                        self.art['button_states'][signal] = now
                        # report
                        self.log.debug('Button: ' + signal + ' - Hold detection - ' + str(hold_time) + 'ms')
                        out = True

            # remember the current state to compare it with the next input
            # state = signal_value

            if not double_use:
                # reset button state if button is not pressed
                if signal_value == 0:
                    self.art['button_states'][signal] = 0

                # set when button was pressed ONYL when the button is pressed, and it was not pressed before
                if signal_value == 1 and self.art['button_states'][signal] == 0:
                    # save timestamp
                    self.art['button_states'][signal] = utils.timestamp_ms()

        # report result
        return out

    # --------------- INPUT Action ----------------------

    # TODO
    def art_braking(self):
    
        self.log.info('BRAKING')

        #if self.art.state == ArtState.ACC_active:
            # self.level_off()
        #    self.acc_deactivation()

            # display trigger
        #    self.acc_set_dspl_trigger()

    def art_warning_button(self):
        self.log.info('Warning Button pressed')

    def lever_off(self):
        self.log.info('Lever OFF pressed')

    def lever_wa(self):
        self.log.info('Lever WA/Resume pressed')

    def lever_up(self):
        self.log.info('Lever PLUS pressed')

    def lever_down(self):
        self.log.info('Lever MINUS pressed')

    # -------------- STATUS ------------------------------

    def status(self):

        out = ''

        if not self.art['ready']:
            out += 'NOT Ready'
        else:
            #out += f"Ready: " + str(self.art['ready'])
            out += str(self.art['state']) + " "

            out += f"\t{self.vehicle_msgs['signals']['V_ANZ']} km/h "


        return out
