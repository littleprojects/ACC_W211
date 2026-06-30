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

import threading

from enum import Enum
from queue import Queue
import threading

class ArtState(Enum):
    OFF = 0
    ART_standby= 1
    ART_active = 2
    LIM_standby = 3
    LIM_active = 4


class ArtData:

    def __init__(self, config, log):

        # init CAN Queue's and Flags/Events
        # Vehicle CAN
        self.q_can_c_in = Queue()
        self.q_can_c_out = Queue()
        # Radar CAN
        self.q_radar_in = Queue()
        self.q_radar_out = Queue()
        
        # NEW MSG FLAG
        # self.flag_new_msg = threading.Event() not in use now

        self.state = ArtState.OFF # statemachine
        self.last_state = self.state    #
        
        self.config = config
        self.log = log

        # init CAN Queue's and Flags/Events
        # Vehicle CAN

        # Todo: INIT Queues and Flags here
        self.q_can_c_in = Queue()
        self.q_can_c_out = Queue()
        # Radar CAN
        self.q_radar_in = Queue()
        self.q_radar_out = Queue()

    def get_state(self):
        # Todo: thread protection
        return self.state

    def set_state(new_state):
        # Todo state change if statemachine and thread protection
        # trigger event at state change or just return TRUE if a statechange happened
        pass