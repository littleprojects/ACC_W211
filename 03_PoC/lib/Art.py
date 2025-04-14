

class Art:

    def __init__(self, config, log):

        # store config
        self.config = config

        # logging
        self.log = log

        # output signals with default values
        self.art_default_msg = {
            # ART_250
            'DYN_UNT': 0,   # dynamic downshift suppression
            'BL_UNT': 0,    # breathtaking suppression
            'ART_BRE': 0,   # ART breaks
            'ART_OK': 0,    # ART ok
            'SLV_ART': 0,   # shift lines adaptation
            'CAS_REG': 0,   # City assist is active
            'MDYN_ART': 0,  # dynamic engine moment
            'MPAR_ART': 0,  # parity
            'ART_REG': 0,   # ART is active
            'LIM_REG': 0,   # limiter is activ
            'M_ART': 0,     # [Nm] engine moment
            'BZ250h': 0,     # msg counter 4bit = 0-15
            'MBRE_ART': 0,  # [Nm] break moment
            'GMIN_ART': 0,  # minimum gear
            'GMAX_ART': 0,  # maximum gear
            'AKT_R_ART': 0,  # shift down request from art

            # ART_258
            'ART_ERROR': 0,     # ART error code
            'ART_INFO': 0,      # ART info light
            'ART_WT': 0,        # ART warning sound
            'S_OBJ': 0,         # standing object detected
            'ART_DSPL_EIN': 0,  # ART display on
            'V_ART': 0,         # [kph] ART set speed
            'ABST_R_OBJ': 0,    # [m] distance to relevant object
            'SOLL_ABST': 0,     # [m] distance to relevant object
            'TM_EIN_ART': 0,    # ART cruise control activ
            'ART_DSPL_BL': 0,   # blink speed control
            'ART_SEG_EIN': 0,   # show speed segments on display
            'OBJ_ERK': 0,       # object detected
            'ART_EIN': 0,       # ART on
            'ART_DSPL_LIM': 0,  # show: --- on display
            'ART_VFBR': 0,      # show: ART off
            'ART_DSPL_PGB': 0,  # show: winter tire speed reached
            'V_ZIEL': 0,        # [kph] target speed on segment display
            'ASSIST_FKT_AKT': 0,  # active function - always 0
            'AAS_LED_BL': 0,    # LED blinking
            'OBJ_AGB': 0,       # object offer adaptive cc - always 0
            'ART_ABW_AKT': 0,   # warnings are switched on
            'ART_REAKT': 0,     # reactivation of ART after error
            'ART_UEBERSP': 0,   # ART passive
            'ART_DSPL_NEU': 0,  # show ART display again for a short time
            'ASSIST_ANZ_V2': 0,  # assist display request - always 0
            'CAS_ERR_ANZ_V2': 0,  # CAS display request - always 0
        }

        # create a copy of the default values - so default can restore anytime
        self.art_msg = self.art_default_msg.copy()

        self.BZ250h = 0 # Botschaftzähler / Message counter 0-15

        self.vehicle_msgs = {'msgs': {},    # msg timestamps in [ms]
                            'signals': {},  # signals as dict
                            'ready': 0      # ready Flag by CANhandler
                            }

        """
        # dict to objs
        class DictObj:
        def __init__(self, in_dict:dict):
            assert isinstance(in_dict, dict)
            for key, val in in_dict.items():
                if isinstance(val, (list, tuple)):
                   setattr(self, key, [DictObj(x) if isinstance(x, dict) else x for x in val])
                else:
                   setattr(self, key, DictObj(val) if isinstance(val, dict) else val)
        """

    def update_input(self, vehicle_msgs):

        # store / update data
        self.vehicle_msgs = vehicle_msgs

        # todo: ready check here
        # todo: check for switch on / off commands

    def update_bz(self):

        # increment msg counter
        self.BZ250h += 1

        # reset of overflow (4 bit = 0-15)
        if self.BZ250h > 15:
            self.BZ250h = 0

        # update in dict
        self.art_msg['BZ250h'] = self.BZ250h

    def get_can_data(self):

        #self.read_check()

        # increment can msg counter (BZ - BotschaftsZähler)
        self.update_bz()

        return self.art_msg



