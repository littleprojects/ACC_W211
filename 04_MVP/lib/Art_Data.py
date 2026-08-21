"""
ART/ACC Data and Config

This class will handle the data exchange between the different module.

- read and write with thread save methods
- queues for CAN data
- locks and dict (deep) copy for other data
- API for other modules to get and set data (like to display the data with Streamlit)

Data:
- CAN Data
    - Vehicle CAN
    - Radar CAN

    
ToDo:

"""

import copy
import threading

from lib import Logger
from lib.Storage import Storage

from enum import Enum
from queue import Queue


class ArtState(Enum):
    OFF = 0
    ACC_standby= 1
    ACC_active = 2
    LIM_standby = 3
    LIM_active = 4


class ArtData:

    def __init__(self, config):

        self.config = config
        self.log = Logger.Log('ArtData', config=config).get_logger()

        # init CAN Queue's and Flags/Events
        # Vehicle CAN
        self.q_can_c_in = Queue()
        self.q_can_c_out = Queue()
        # Radar CAN
        self.q_radar_in = Queue()
        self.q_radar_out = Queue()
        
        # NEW MSG FLAG
        # self.flag_new_msg = threading.Event() not in use now

        # state machine
        self._state = ArtState.OFF # statemachine
        #self._last_state = self._state    
        self._lock_state = threading.Lock()  # threading lock variable for state changes

        # default Values
        self._CONST_default_values = {
            
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

            # Values  for the ACC controller
        }

        # ART values to send out
        # init as a copy of the default values
        self._art_msg = copy.deepcopy(self._CONST_default_values)

        self._BZ250h = 0  # Message counter 0-15 (BZ = BotschaftZähler)
        self._lock_art_msg = threading.Lock()  # threading lock variable for ART values

        # CAN C signals and messages
        self._vehicle_msgs = {
            'msgs': {},  # msg timestamps in [ms]
            'signals': {},  # signals as dict
        }
        self._lock_vehicle_msgs = threading.Lock()  # threading lock variable for vehicle CAN msgs

        # Radar CAN signals and messages
        self._radar_msgs = {
            'msgs': {},  # msg timestamps in [ms]
            'signals': {},  # signals as dict
        }
        self._lock_radar_msgs = threading.Lock()  # threading lock variable for radar CAN msgs

        # ART internal states to share
        self._art_states = {}
        self._lock_art_states = threading.Lock()  # threading lock variable for ART states

        # callbacks to notify other modules (e.g. Art.can_update)
        self._can_update_callbacks = []

        # storage for persistent data
        self._persistent_data = {
            'warning_state': 0,
        }       

        # load waring_state from persistent storage (STORAGE lib)
        self.Store = Storage(self.config.persistent_storage_file, self._persistent_data, self.log)
        # restore last warning state
        self._art_msg['ART_ABW_AKT'] = self.Store.data['warning_state']

    # ------ State Machine SET GET -----------------------------
    def get_state(self):
        # thread protection
        with self._lock_state:
            return self._state

    def set_state(self, new_state):
        # thread protection
        with self._lock_state:

            # state change detection
            if new_state != self._state:                
                self.log.info(f"State changed from {self._state} to {new_state}")

                #self._last_state = self._state  # remember last state, just in case we need it
                self._state = new_state

                # Todo trigger event at state change or just return TRUE if a statechange happened

    # ------ ART Values SET GET Methods -----------------------------
    def get_art_msg(self):
        # thread protection
        with self._lock_art_msg:
            # TODO: signal limit checks
            
            return copy.deepcopy(self._art_msg) # return a copy of the dict
        
    def set_art_msg(self, new_values):
        # thread protection
        with self._lock_art_msg:
            self._art_msg.update(new_values)  # update the dict with new values

    # ------ Vehicle CAN C SET GET Methods -----------------------------
    def get_vehicle_msgs(self):
        # thread protection
        with self._lock_vehicle_msgs:
            return copy.deepcopy(self._vehicle_msgs)  # return a copy of the dict
        
    def set_vehicle_msgs(self, new_msgs):
        # thread protection
        with self._lock_vehicle_msgs:
            #self.log.debug(f"Vehicle CAN: {self._vehicle_msgs}")            
            self._vehicle_msgs['msgs'].update(new_msgs['msgs'])  # update the dict with new values
            self._vehicle_msgs['signals'].update(new_msgs['signals'])  # update the dict with new values          

            #TODO check for cancel conditions

            # clean Speed
            if 'V_ANZ' in new_msgs['signals']:
                self._vehicle_msgs['signals']['V_ANZ'] = round(new_msgs['signals']['V_ANZ'], 1)

            # notify registered callbacks that vehicle CAN was updated
            for cb in list(self._can_update_callbacks):
                try:
                    cb(new_msgs['signals'])
                except Exception as e:
                    # swallow exceptions from callbacks to avoid breaking caller
                    self.log.warning(f"Can't call callback: {e}")
                    pass

    def register_can_update_callback(self, callback):
        """Register a callable to be invoked when vehicle CAN msgs are updated.

        The callback will be called with one argument: the new_msgs dict.
        Example: art_data.register_can_update_callback(Art.can_update)
        """
        if callable(callback):
            self._can_update_callbacks.append(callback)
            self.log.debug('CAN update callback registered')


    # ------ Radar CAN SET GET Methods -----------------------------
    def get_radar_msgs(self):
        # thread protection
        with self._lock_radar_msgs:
            return copy.deepcopy(self._radar_msgs)  # return a copy of the dict

    def set_radar_msgs(self, new_msgs):
        # thread protection
        with self._lock_radar_msgs:
            self._radar_msgs['msgs'].update(new_msgs['msgs'])  # update the dict with new values
            self._radar_msgs['signals'].update(new_msgs['signals'])  # update the dict with new values

    # ------ ART States SET GET Methods -----------------------------
    def get_art_states(self):
        # thread protection
        with self._lock_art_states:
            return copy.deepcopy(self._art_states)  # return a copy of the dict

    def set_art_states(self, new_states):
        # thread protection
        with self._lock_art_states:
            self._art_states.update(new_states)  # update the dict with new values
            # convert state to string for JSON serialization
            self._art_states['state'] = str(self._art_states['state'])

    # ------ write warning state to persitent memory -----------------------------

    def save_warning_state(self, warning_state):

        self._persistent_data['warning_state'] = warning_state

        self.Store.write(self._persistent_data)

    # ------ status log -----------------------------
    def status(self):
        # get signals
        can_c_data = self.get_vehicle_msgs()
        
        out = f"ART: msgs {len(can_c_data['msgs'])}, values {len(can_c_data['signals'])} "
        # TODO: add more details like msg count, signal count, etc.
        
        return out
        