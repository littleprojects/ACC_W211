import cantools

from lib import utils
from lib.Logger import Log


class CanHandler:

    def __init__(self, config, q_cc_in, q_cc_out, update_function, filter_msg_id_list = None):
        # cc = Can Car

        self.config = config
        
        # Logger
        self.log = Log('CP_'+self.config.channel, config=self.config).get_logger()

        # queues CAN C
        self.q_cc_in = q_cc_in
        self.q_cc_out = q_cc_out

        # CAN database
        self.dbc = None

        # update function
        self.update_function = update_function

        # filter List:
        # white list of needed msg id's to process in hex or decimal [ 0x200, 786]
        self.filter_msg_id_list = filter_msg_id_list

        # load DBC
        try:
            self.dbc = cantools.database.load_file(self.config.dbc)
        except Exception as e:
            self.log.critical('Cant load DBC: ' + str(e))
            exit()

        # CAN statistic
        self.stats = {
            'in': 0,
            'out': 0
        }

    def parse_msgs(self):

        # decode msgs
        new_can_msgs = False        

        # process the msgs in q_in
        while not self.q_cc_in.empty():


            new_msgs = {
                'msgs': {},  # msg timestamps in [ms]
                'signals': {},  # signals as dict
            }

            msg = self.q_cc_in.get()
            self.q_cc_in.task_done()

            # ignore unneeded can msgs
            if self.filter_msg_id_list is not None:
                if msg.arbitration_id not in self.filter_msg_id_list:
                    continue    # skip this msg

            vehicle_msg_id = hex(msg.arbitration_id)

            # set receive timestamp
            new_msgs['msgs'].update({vehicle_msg_id: utils.timestamp_ms()})

            # decode msg
            try:
                decode_msg = self.dbc.decode_message(msg.arbitration_id, msg.data)
            except Exception as e:
                # could happen if there are CAN Errors on the bus
                self.log.critical('Cant decode msg: ' + str(e))
                continue

            # ignore empty msgs
            if len(decode_msg) == 0:
                continue

            # new msgs received
            #new_can_msgs = True

            # all signals in the msg
            for key in decode_msg.keys():
                signal_name = key
                signal_data = decode_msg[key]

                # update new msgs
                new_msgs['signals'].update({signal_name: signal_data})

            # update data
            self.update_function(new_msgs)  # call the update function with the new msgs
            
            #self.log.debug(f"update Msg {new_msgs}")

            # TODO MDF Logging
            #mdf log
            #self.mdf.add_signals(decode_msg)

            # update all msgs
            #self.vehicle_msg['signals'].update(new_msgs)

            # update msg counter
            self.stats['in'] += 1

        # update ART at new messages
        #if new_can_msgs:
            # send all msgs
            # self.Art.update_input(self.vehicle_msg)

            # send new msgs and all
            #self.Art.update_input(new_msgs, self.vehicle_msg)

            # Todo?: instant update needed for quick changes -> request quick CAN response
            # maybe with a response to the update process or external event

    def send_msg(self, msg_id, msg_data):

        # if self.config.can_0_send: # TODO: do in CAN class

        # write msg to output queue dict {'id': arbitration_id, 'data': msg_binary_data}
        self.q_cc_out.put({'id': msg_id, 'data': msg_data})

        self.stats['out'] += 1

    def status(self):
        # get signals from
        out = f"Rx {self.stats['in']}, Tx {self.stats['out']} "
        #self.log.info(out)
        return out
        
    """
    # 10 Hz triggered
    def create_out_msgs(self):

        # triggers output calculation
        art_data = self.Art.tick_10hz()

        # todo CAN msg value check -> value have to fit to can msg

        # create ART_250 msg data
        self.art_250_data = self.dbc.encode_message(0x250, {
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
        self.art_258_data = self.dbc.encode_message(0x258, {
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

        # mdf log
        self.mdf.add_signals(art_data, signal_prefix='art_')
    """
    
    # special function for CAN_C only - because the msgs are only in this DBC
    def send_art_msg(self, art_msg_data):

        # NOTE: create ART output - ONLY in CAN_C DBC - ONLY for CAN_C

        art_data = art_msg_data

        # create ART_250 msg binary data
        art_250_data = self.dbc.encode_message(0x250, {
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

        # create ART_258 msg binary data
        art_258_data = self.dbc.encode_message(0x258, {
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

        # write msg to output queue
        # dict {'id': arbitration_id, 'data': msg_binary_data}
        self.q_cc_out.put({'id': 0x250, 'data': art_250_data})
        self.q_cc_out.put({'id': 0x258, 'data': art_258_data})

        self.stats['out'] += 2


    """
    def status_log(self):
        # get signals from
        art_stats = self.Art.status_log()

        out = ''

        if art_stats['ready']:

            out = f"R_{art_stats['state']} "
            out += f"\tV_ANZ/ART/Ziel: {round(self.vehicle_msg['signals']['V_ANZ'], 1)}/{art_stats['V_ART']}/{art_stats['V_ZIEL']} "

            # ACC
            if art_stats['state'] == ArtState.ACC_active:
                # status log output
                #out +=f"\tV_ANZ/ART/Ziel: {round(self.vehicle_msg['signals']['V_ANZ'], 1)}/{art_stats['V_ART']}/{art_stats['V_ZIEL']} "
                out += f"\tG_min/is/max: {art_stats['art_GMIN']}/{self.vehicle_msg['signals']['GIC']}/{art_stats['art_GMAX']}"
                out += f"\tM_FV/M_ART/MBRE_ART: {round(self.vehicle_msg['signals']['M_FV'], 1)}/{art_stats['M_ART']}/{art_stats['MBRE_ART']} "
                out += f"\tP,I,D: {art_stats['pid_p']}, {art_stats['pid_i']}, {art_stats['pid_d']} ({art_stats['pid_lc']}) "
                out += f"M_ART: {art_stats['M_ART']}"


            # LIMITER
            if art_stats['state'] == ArtState.LIM_active:
                out += f"\tM_FV/_MAX/_ART: {round(self.vehicle_msg['signals']['M_FV'], 1)}/{art_stats['lim_max_moment']}/{art_stats['M_ART']} "

        else:
            # status log output
            out = f"Not Ready reason: {art_stats['ready_error']} \t{art_stats['state']} "
            out += f"\tCAN_0: Rx {self.stats['in']}, Tx {self.stats['out']} "

        self.log.info(out)
        """