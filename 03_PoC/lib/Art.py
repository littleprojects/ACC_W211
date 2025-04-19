"""
ART/DTS Class

- check inputs
- state machine
- Controller for
    - Cruise Control (VV)
    - Adaptive Cruise Control (ACC)
    - Limiter (Lim)

"""

import math
from enum import Enum
from lib import utils


# ART Statemachine states class
class ArtState(Enum):
    ACC = 1  # init ACC/CC function
    LIM = 2  # Limiter function
    ACC_active = 3
    LIM_active = 4


class ArtObj:
    def __init__(self):

        # ART init values
        self.ready = False          # is not ready
        self.state = ArtState.ACC   # statemachine
        self.dspl_trigger_ts = 0    # timestamp of display trigger


class Art:

    def __init__(self, config, log):

        # store config
        self.config = config

        # logging
        self.log = log

        # output signals with default values
        self.art_default_msg = {
            # ART_250
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

            # ART_258
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
            'ART_ABW_AKT': 0,  # warnings are switched on TODO load from memory
            'ART_REAKT': 0,  # reactivation of ART after error
            'ART_UEBERSP': 0,  # ART passive
            'ART_DSPL_NEU': 0,  # show ART display again for a short time
            'ASSIST_ANZ_V2': 0,  # assist display request - always 0
            'CAS_ERR_ANZ_V2': 0,  # CAS display request - always 0
        }

        # create a copy of the default values - so default can restore anytime
        self.art_msg = self.art_default_msg.copy()

        self.BZ250h = 0  # Botschaftzähler / Message counter 0-15

        # can signals and messages
        self.vehicle_msgs = {
            'msgs': {},  # msg timestamps in [ms]
            'signals': {},  # signals as dict
        }

        # init ART States
        self.art = ArtObj()

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

        self.log.info('INIT ACC - NOT READY')

    def update_input(self, new_msgs, all_data):

        # print(new_msgs)

        if self.art.ready:

            # look for key events in new data
            for key in new_msgs.keys():
                signal_name = key
                signal_data = new_msgs[key]

                """
                # ACC/CC
                if self.art.state == ArtState.ACC:
                    # check for ACC/CC activation

                    # Reset/set speed/+1 kph (Wiederaufnahme)
                    if signal_name == 'WA' or signal_name == 'S_PLUS_B' or signal_name == 'S_MINUS_B':
                        # check stick is valid (WH_UP) AND speed over 30 kph AND WA active
                        if signal['WH_UP'] == 0 and signal['V_ANZ'] >= 30.0 and signal_data == 1:
                            # active ACC/CC and reset/set speed/+1 speed
                            # set speed
                            if self.art_msg['V_ART'] == 0:
                                self.art_msg['V_ART'] = signal['V_ANZ']

                            # no reset speed at speed up or down -> just use current speed
                            if signal_name == 'S_MINUS_B' or signal_name == 'S_PLUS_B':
                                self.art_msg['V_ART'] = signal['V_ANZ']

                            # use last speed
                            self.acc_activation()

                    # todo check for switch to LIM mode
                    pass
                """



                # ACC/CC active
                if self.art.state == ArtState.ACC_active:
                    # check for ACC/CC deactivation
                    # BRAKING
                    if signal_name == 'SFB' and signal_data == 1:
                        self.art_braking()

                """
                # Lim
                if self.art.state == ArtState.LIM:
                    # todo check for Limiter activation
                    # todo check for switch to ACC/CC mode
                    pass

                # Lim active
                if self.art.state == ArtState.LIM_active:
                # todo check for LIM deactivatio
                # todo check for LIM adjustments
                    pass
                """

                # state independent adjustments

                if signal_name == ['AUS']:
                    print(new_msgs)

                # level off
                if signal_name == ['AUS'] and signal_data == 1:
                    self.lever_off()

                # +1 kph is pressed and was not pressed before
                if signal_name == 'WA' and signal_data == 1 and self.vehicle_msgs['signals']['WA'] == 0:
                    self.lever_resume()

                # Round up (+10) is pressed and was not pressed before
                if signal_name == 'S_PLUS_B' and signal_data == 1 and self.vehicle_msgs['signals']['S_PLUS_B'] == 0:
                    self.lever_up()

                # Round down (-10) is pressed and was not pressed before
                if signal_name == 'S_MINUS_B' and signal_data == 1 and self.vehicle_msgs['signals']['S_MINUS_B'] == 0:
                    self.lever_down()

                # ART warning ON/OFF button and was not pressed before
                if signal_name == 'ART_ABW_BET' and signal_data == 1 and self.vehicle_msgs['signals']['ART_ABW_BET'] == 0:
                    self.art_warning_button()

                if signal_name == 'CRASH':
                    # crash detected
                    if signal_data == 1:
                        self.log.critial('CRASH detected')
                        self.reset_to_default()

                # Limiter is activ
                if signal_name == 'VMAX_AKT' and signal_data == 1:
                    # todo LIMITER
                    pass

            # update msg storage
            #self.vehicle_msgs['signals'].update({signal_name: signal_data})

        # update dataset
        self.vehicle_msgs.update(all_data)

        # basic ready check
        self.is_ready()

    def art_warning_button(self):
        self.log.debug('Warning Button pressed')

        # if ART warning button pressed toggle warning status
        if self.art_msg['ART_ABW_AKT'] == 0:
            self.art_msg['ART_ABW_AKT'] = 1
            self.log.debug('Activate warnings')
        else:
            self.art_msg['ART_ABW_AKT'] = 0
            self.log.debug('Deactivate warnings')

    def art_braking(self):

        # self.level_off()
        self.acc_deactivation()

        # display trigger
        self.acc_set_dspl_trigger()

    def lever_off(self):
        self.log.debug('Lever off pressed')

        # display trigger
        self.acc_set_dspl_trigger()

        if self.art.state == ArtState.ACC_active:
            self.acc_deactivation()

    # level_resume pressed
    def lever_resume(self):
        self.log.debug('Lever resume pressed')

        # display trigger
        self.acc_set_dspl_trigger()

        signal = self.vehicle_msgs['signals']

        # ACC ready -> activation
        if self.art.state == ArtState.ACC:
            # check for min speed
            if signal['V_ANZ'] < int(self.config.acc_min_speed):
                self.log.warning('Cant enable ACC: too slow')
                # trigger '---' display
                self.acc_set_dspl_lim_trigger()
                return False

            # check for max speed
            if signal['V_ANZ'] > int(self.config.acc_max_speed):
                self.log.warning('Cant enable ACC: too fast')
                # trigger '---' display
                self.acc_set_dspl_lim_trigger()
                return False

            # level ok
            if signal['WH_UP'] == 1:
                self.log.warning('Cant enable ACC: Selector Level implausible')
                return False

            # set speed only if speed was not set yet
            if self.art_msg['V_ART'] == 0:
                # round current speed up and set as target speed
                self.art_msg['V_ART'] = math.ceil(signal['V_ANZ'])

                self.log.info('ACC: set speed to ' + str(self.art_msg['V_ART']))

            # and power
            self.acc_activation()

        # ACC active
        if self.art.state == ArtState.ACC_active:
            #  speed +1
            self.art_msg['V_ART'] += 1

            # upper limit
            if self.art_msg['V_ART'] > self.config.acc_max_speed:
                self.art_msg['V_ART'] = self.config.acc_max_speed

            self.log.info('ACC: set speed to ' + str(self.art_msg['V_ART']))
        pass

    def lever_up(self):
        self.log.debug('Lever up pressed')

        # display trigger
        self.acc_set_dspl_trigger()

        signal = self.vehicle_msgs['signals']

        # ACC ready -> activation
        if self.art.state == ArtState.ACC:
            # if signal['V_ANZ'] < 30.0:
            if signal['V_ANZ'] < int(self.config.acc_min_speed):
                self.log.warning('Cant enable ACC: too slow')
                # trigger '---' display
                self.acc_set_dspl_lim_trigger()
                return False

            # check for max speed
            if signal['V_ANZ'] > int(self.config.acc_max_speed):
                self.log.warning('Cant enable ACC: too fast')
                # trigger '---' display
                self.acc_set_dspl_lim_trigger()
                return False

            # lever check
            if signal['WH_UP'] == 1:
                self.log.warning('Cant enable ACC: Selector Level implausible')
                return False

            # set target speed to current speed
            self.art_msg['V_ART'] = math.ceil(signal['V_ANZ'])

            self.log.info('ACC: set speed to ' + str(self.art_msg['V_ART']))

            # and power
            self.acc_activation()

        # ACC active
        if self.art.state == ArtState.ACC_active:
            #  set speed to next tens +10
            speed = self.art_msg['V_ART'] + 1
            self.art_msg['V_ART'] = math.ceil(speed/10)*10

            # upper limit
            if self.art_msg['V_ART'] > self.config.acc_max_speed:
                self.art_msg['V_ART'] = self.config.acc_max_speed

            self.log.info('ACC: set speed to ' + str(self.art_msg['V_ART']))

    def lever_down(self):
        self.log.debug('Lever down pressed')

        # display trigger
        self.acc_set_dspl_trigger()

        signal = self.vehicle_msgs['signals']

        # ACC ready -> activation
        if self.art.state == ArtState.ACC:
            # if signal['V_ANZ'] < 30.0:
            if signal['V_ANZ'] < int(self.config.acc_min_speed):
                self.log.warning('Cant enable ACC: to slow')
                # trigger '---' display
                self.acc_set_dspl_lim_trigger()
                return False

            # check for max speed
            if signal['V_ANZ'] > int(self.config.acc_max_speed):
                self.log.warning('Cant enable ACC: too fast')
                # trigger '---' display
                self.acc_set_dspl_lim_trigger()
                return False

            # lever check
            if signal['WH_UP'] == 1:
                self.log.warning('Cant enable ACC: Selector Level implausible')
                return False

            # set target speed to current speed
            # round down and set
            self.art_msg['V_ART'] = math.floor(signal['V_ANZ'])

            self.log.info('ACC: set speed to ' + str(self.art_msg['V_ART']))

            # and power
            self.acc_activation()

        # ACC active
        if self.art.state == ArtState.ACC_active:
            #  flor speed to lower tens -10
            speed = self.art_msg['V_ART'] - 1
            self.art_msg['V_ART'] = math.floor(speed/10)*10

            # lower limit
            if self.art_msg['V_ART'] < self.config.acc_min_speed:
                self.art_msg['V_ART'] = self.config.acc_min_speed

            self.log.info('ACC: set speed to ' + str(self.art_msg['V_ART']))

    def acc_activation(self):
        self.log.debug('ACC activation')

        # activate ACC
        self.art.state = ArtState.ACC_active

        # todo set outputs
        # display ein
        self.art_msg['ART_SEG_EIN'] = 1
        # read distance ajust
        # calc distance

    def acc_calc(self):
        # self.log.debug('ACC calc')

        # basic ready check also after some time
        self.is_ready()

        # double
        # check braking
        # min limit
        # max limit
        # switch off if car is too slow

        # V_ZIEL or in radar calc
        self.art_msg['V_ZIEL'] = self.art_msg['V_ART']

        # todo ART_VFBR (VerFügBaR - available)
        # goes off [0] if speed it too slow (trigger dspy), recover [1] after trigger time
        # blocks reactivation if state is 0 ???

        # ART overwrite by driver
        # ART_UBERSP

        # ART channels
        # TM_EIN_ART - ART is active
        # ART_REG
        # M_ART
        # MBRE_ART
        # ART_BRE
        # BL_UNT
        # MPAR_ART - parity bit at changes
        # GMIN_ART
        # GMAX_ART
        # AKT_R_ART
        # ART_ERROR 4 - External Error

        # LIM_REG

        # update safety distance
        self.acc_calc_distance()

        # general warnings
        self.acc_calc_warnings()

        # calc only when acc is ready
        if self.art.state == ArtState.ACC_active:

            # todo error calc and output
            if self.art_msg['ART_ABW_AKT'] == 1:
                # warnings are on
                # set outputs
                pass
            else:
                # warnings are off
                # set outputs
                pass

            pass

        # reset trigger
        self.acc_reset_trigger()

    def acc_deactivation(self):

        # disable segment display
        self.art_msg['ART_SEG_EIN'] = 0

        self.log.debug('ACC deactivation')

        # switch to state ACC ready
        self.art.state = ArtState.ACC

        # todo reset outputs

    # todo calc warnings
    def acc_calc_warnings(self):
        # todo car too close
        # todo delta speed too big
        # ART_INFO -> Light
        # ART_WT -> Warning (Ton) Sound
        # AAS_LED_BL -> LED ACC blinking -> check/test
        pass

    def radar(self):
        # Data
        # S_OBJ - standing object detected
        # ABST_R_OBJ - distance to relevant object [m]
        # OBJ_ERK - object detected
        # V_ZIEL - target vehicle speed [kph]
        # OBJ_AGB - Object offer acc ? -> check
        # ART_REAKT - show reaktivation after error -> check/test
        pass

    def acc_calc_distance(self):
        # get vehicle speed

        # is signal already in vehcilse data
        if 'V_ANZ' in self.vehicle_msgs['signals']:

            speed = self.vehicle_msgs['signals']['V_ANZ']
            # round up
            speed = math.ceil(speed)

            # todo get distance ajust value

            # calc distance in [m]
            # todo do the right calc
            dist = speed / 2

            # round up
            dist = math.ceil(dist)

            # keep a minimum distance of 3 meter
            dist = max(3, dist)

            # zero dist at standstill
            if speed == 0:
                dist = 0

            # and set new distance
            self.art_msg['SOLL_ABST'] = dist

    def acc_set_dspl_trigger(self):
        # set art show trigger in display
        self.art_msg['ART_DSPL_NEU'] = 1

        # display switch to art page
        self.art_msg['ART_DSPL_EIN'] = 1
        self.art.dspl_trigger_ts = utils.ts_ms()
        # needs to reset after a some time

        # clear blinking '---' this is set later if needed
        self.art_msg['ART_DSPL_LIM'] = 0
        self.art_msg['ART_DSPL_BL'] = 0

    def acc_set_dspl_lim_trigger(self):

        # show --- in display if speed is too slow or too fast
        self.art_msg['ART_DSPL_LIM'] = 1
        # blink display
        self.art_msg['ART_DSPL_BL'] = 1

    def acc_reset_trigger(self):
        # reset only if a trigger is active
        if self.art.dspl_trigger_ts != 0:

            # get current time
            now = utils.ts_ms()

            # to calc time delta
            delta_time = now - self.art.dspl_trigger_ts

            # time is up
            if delta_time >= self.config.art_trigger_time:
                # clear
                self.art_msg['ART_DSPL_EIN'] = 0
                self.art_msg['ART_DSPL_LIM'] = 0
                self.art_msg['ART_DSPL_BL'] = 0
                # clear trigger
                self.art.dspl_trigger_ts = 0

    def get_can_data(self):

        # do the magic
        self.acc_calc()
        # todo self.lim_calc()

        # increment can msg counter (BZ - BotschaftsZähler)
        self.update_bz()

        return self.art_msg

    def update_bz(self):

        # increment msg counter
        self.BZ250h += 1

        # reset of overflow (4 bit = 0-15)
        if self.BZ250h > 15:
            self.BZ250h = 0

        # update in dict
        self.art_msg['BZ250h'] = self.BZ250h

    def reset_to_default(self):
        # if art is not ready anymore
        # if self.art.ready is not True:

        self.log.info('RESET to default')

        # reset state
        self.art.state = ArtState.ACC

        # save target speed
        target_speed = self.art_msg['V_ART']

        # load default values
        self.art_msg = self.art_default_msg.copy()
        self.art_msg['V_ART'] = target_speed

    def set_art_ready(self):

        if not self.art.ready:
            self.log.info('READY')

            # set
            self.art_msg['ART_OK'] = 1
            self.art_msg['ART_EIN'] = 1
            self.art_msg['TM_EIN_ART'] = 1
            self.art_msg['ART_VFBR'] = 1

            # if no chancel condition quit - we a are save to go
            self.art.ready = True

    def is_ready(self):
        """
        This function checks the CAN msgs and signals if everything is ok
        """

        ts_now = utils.ts_ms()

        # all MSG id there they need to check
        needed_msg_id_list = [
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
            '0x328',  # BS
        ]

        # check all needed CAN messages (from list) received
        all_msgs_found = True

        for msg_id in needed_msg_id_list:
            if not (msg_id in self.vehicle_msgs['msgs']):
                all_msgs_found = False

                # self.log.debug('Checker: ID ' + msg_id + ' not found')

                # stop loop
                break

        # NOT all msgs found -> NOT READY
        if not all_msgs_found:

            if self.art.ready:
                self.art.ready = False
                self.log.debug('Checker: Msgs incomplete')
                # reset default output values
                self.reset_to_default()

            return False

        # no MSG ts is too old
        all_msg_in_time = True

        # max_delay = 500  # ms
        max_delay = int(self.config.max_msg_delay)

        for msg_id in needed_msg_id_list:
            ts_last_msg = self.vehicle_msgs['msgs'][msg_id]

            # delay in ms
            delay = ts_now - ts_last_msg

            if delay > max_delay:
                all_msg_in_time = False

                # self.log.debug('Checker: ' + msg_id + ' is to old - ' + str(delay) + ' ms')

                # end loop
                break

        # NOT all msg in time -> NOT READY
        if not all_msg_in_time:
            if self.art.ready:
                self.art.ready = False
                self.log.warning('Checker: Msgs to old')
                # load default output values
                self.reset_to_default()
            return False

        # Todo: needed Signals are in range check
        # signals = self.vehicle_msgs['signals']

        # Gear is in D
        if 'DRTGTM' in self.vehicle_msgs['signals']:
            if self.vehicle_msgs['signals']['DRTGTM'] != 1:
                if self.art.ready:
                    self.art.ready = False
                    # load default output values
                    self.reset_to_default()
                    self.log.info('Checker: Gear is NOT in D')
                return False
        else:
            # Dataset incomplete
            return False

        # set ready values
        self.set_art_ready()

        return True

# end class ART
