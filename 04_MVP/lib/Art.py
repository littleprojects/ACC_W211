"""
ART/DTS Class

- check inputs
- state machine
- Controller for
    - Cruise Control (VV)
    - Adaptive Cruise Control (ACC)
    - Limiter (Lim)

"""

from lib.Logger import Log

class ART:
    def __init__(self, config, art_data):
        
        self.config = config
        
        # Logger
        self.log = Log('ART', config=config).get_logger()

        self.art_data = art_data
        #self.mdf = mdf

        # ART State Machine
        #self.state_machine = ArtStateMachine(log, config)

        # ART Data
        #self.data = ArtData(log, config)

        # art values
        self.art_values = {}

        # CAN C signals and messages
        self.vehicle_msgs = {
            'msgs': {},  # msg timestamps in [ms]
            'signals': {},  # signals as dict
        }

    def tick_10Hz(self):
        # 10 Hz tick for ART
        # - get data from ART Data
        # - check inputs
        # - state machine
        # - Controller for Cruise Control (CC), Adaptive Cruise Control (ACC), Limiter (Lim)
        # - send CAN messages

        self.log.debug("10Hz tick")

        # load data from ART Data
        self.art_values = self.art_data.get_art_values()
        self.vehicle_msgs = self.art_data.get_vehicle_msgs()
        

        # TODO: do the magic

        # write data back
        self.art_data.set_art_values(self.art_values)
        self.art_data.set_vehicle_msgs(self.vehicle_msgs)
        
