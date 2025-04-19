import cantools

from lib import utils
from lib import check

from lib.Art import Art


class CanHandler:

    def __init__(self, config, log, q_cc_in, q_cc_out, needed_msg_id_list):
        # cc = Can Car

        self.config = config
        self.log = log

        # init ART Class
        self.Art = Art(config, log)

        # queues CAN C
        self.q_cc_in = q_cc_in
        self.q_cc_out = q_cc_out

        # filter List:
        self.needed_msg_id_list = needed_msg_id_list

        # data storage
        self.vehicle_msg = {'msgs': {},
                            'signals': {},
                            'ready': 0
                            }

        # CAN Data
        self.art_250_data = None
        self.art_258_data = None

        # load DBC
        try:
            self.db_0 = cantools.database.load_file(config.can_0_dbc)
        except Exception as e:
            self.log.critical('Cant load DBC: ' + str(e))

    def new_msg(self):

        # decode msgs
        new_can_msgs = False
        new_msgs = {}

        # process the msgs in q_in
        while not self.q_cc_in.empty():

            msg = self.q_cc_in.get()
            self.q_cc_in.task_done()

            # ignore unneeded can msgs
            if msg.arbitration_id not in self.needed_msg_id_list:
                continue

            vehicle_msg_id = hex(msg.arbitration_id)

            # update msg timestamp
            self.vehicle_msg['msgs'].update({vehicle_msg_id: utils.ts_ms()})

            # decode msg
            decode_msg = self.db_0.decode_message(msg.arbitration_id, msg.data)

            # ignore empty msgs
            if len(decode_msg) == 0:
                continue

            # new msgs received
            new_can_msgs = True

            # all signals in the msg
            for key in decode_msg.keys():
                signal_name = key
                signal_data = decode_msg[key]

                # update msg storage all
                # self.vehicle_msg['signals'].update({signal_name: signal_data})
                # update new msgs
                new_msgs.update({signal_name: signal_data})

            # update all msgs
            self.vehicle_msg['signals'].update(new_msgs)

        # update ART at new messages
        if new_can_msgs:
            # send all msgs
            # self.Art.update_input(self.vehicle_msg)

            # send new msgs and all
            self.Art.update_input(new_msgs, self.vehicle_msg)

            # Todo?: instant update needed for quick changes -> request quick CAN response
            # maybe with a response to the update process or external event

    def create_out_msgs(self):

        art_data = self.Art.get_can_data()

        # create ART_250 msg data
        self.art_250_data = self.db_0.encode_message(0x250, {
                'DYN_UNT':  art_data['DYN_UNT'],    # dynamic downshift suppression
                'BL_UNT':   art_data['BL_UNT'],     # breathtaking suppression
                'ART_BRE':  art_data['ART_BRE'],    # ART breaks
                'ART_OK':   art_data['ART_OK'],     # ART ok
                'SLV_ART':  art_data['SLV_ART'],    # shift lines adaptation
                'CAS_REG':  art_data['CAS_REG'],    # City assist is active
                'MDYN_ART': art_data['MDYN_ART'],   # dynamic engine moment
                'MPAR_ART': art_data['MPAR_ART'],   # parity
                'ART_REG':  art_data['ART_REG'],    # ART is active
                'LIM_REG':  art_data['LIM_REG'],    # limiter is activ
                'M_ART':    art_data['M_ART'],      # [Nm] engine moment
                'BZ250h':   art_data['BZ250h'],     # msg counter 4bit = 0-15
                'MBRE_ART': art_data['MBRE_ART'],   # [Nm] break moment
                'GMIN_ART': art_data['GMIN_ART'],   # minimum gear
                'GMAX_ART': art_data['GMAX_ART'],   # maximum gear
                'AKT_R_ART': art_data['AKT_R_ART'],  # shift down request from art
            }
        )

        # create ART_258 msg data
        self.art_258_data = self.db_0.encode_message(0x258, {
            'ART_ERROR':    art_data['ART_ERROR'],      # ART error code
            'ART_INFO':     art_data['ART_INFO'],       # ART info light
            'ART_WT':       art_data['ART_WT'],         # ART warning sound
            'S_OBJ':        art_data['S_OBJ'],          # standing object detected
            'ART_DSPL_EIN': art_data['ART_DSPL_EIN'],   # ART display on
            'V_ART':        art_data['V_ART'],          # [kph] ART set speed
            'ABST_R_OBJ':   art_data['ABST_R_OBJ'],     # [m] distance to relevant object
            'SOLL_ABST':    art_data['SOLL_ABST'],      # [m] distance to relevant object
            'TM_EIN_ART':   art_data['TM_EIN_ART'],     # ART cruise control activ
            'ART_DSPL_BL':  art_data['ART_DSPL_BL'],    # blink speed control
            'ART_SEG_EIN':  art_data['ART_SEG_EIN'],    # show speed segments on display
            'OBJ_ERK':      art_data['OBJ_ERK'],        # object detected
            'ART_EIN':      art_data['ART_EIN'],        # ART on
            'ART_DSPL_LIM': art_data['ART_DSPL_LIM'],   # show: --- on display
            'ART_VFBR':     art_data['ART_VFBR'],       # show: ART off
            'ART_DSPL_PGB': art_data['ART_DSPL_PGB'],   # show: winter tire speed reached
            'V_ZIEL':       art_data['V_ZIEL'],         # [kph] target speed on segment display
            'ASSIST_FKT_AKT': art_data['ASSIST_FKT_AKT'],  # active function - always 0
            'AAS_LED_BL':   art_data['AAS_LED_BL'],     # LED blinking
            'OBJ_AGB':      art_data['OBJ_AGB'],        # object offer adaptive cc - always 0
            'ART_ABW_AKT':  art_data['ART_ABW_AKT'],    # warnings are switched on
            'ART_REAKT':    art_data['ART_REAKT'],      # reactivation of ART after error
            'ART_UEBERSP':  art_data['ART_UEBERSP'],    # ART passive
            'ART_DSPL_NEU': art_data['ART_DSPL_NEU'],   # show ART display again for a short time
            'ASSIST_ANZ_V2': art_data['ASSIST_ANZ_V2'],  # assist display request - always 0
            'CAS_ERR_ANZ_V2': art_data['CAS_ERR_ANZ_V2'],  # CAS display request - always 0
            }
        )

        # self.log.debug('ART 0x250 Msg data: ' + str(self.art_250_data))
        # self.log.debug('ART 0x258 Msg data: ' + str(self.art_258_data))

    def send_status_msg(self):

        # create output
        self.create_out_msgs()

        if self.config.can_0_send:
            # write msg to output queue
            # dict {'id': arbitration_id, 'data': msg_binary_data}
            self.q_cc_out.put({'id': 0x250, 'data': self.art_250_data})
            self.q_cc_out.put({'id': 0x258, 'data': self.art_258_data})


