"""
ART/DTS Class

- check inputs
- state machine
- Controller for
    - Cruise Control (VV)
    - Adaptive Cruise Control (ACC)
    - Limiter (Lim)


- Todos:
    - Limit acceleration by corner radius

"""

import math
from enum import Enum

from lib import utils

from lib.Pid import PID



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
        # inputs

        self.braking = 0            # is driver braking
        self.lever_wa_pressed = 0   # is WA pressed
        self.lever_up_pressed = 0   # is UP pressed
        self.lever_dw_pressed = 0   # is DOWN pressed
        self.lever_off_pressed = 0  # is OFF pressed
        self.level_lim_pressed = 0  # is LIMITER pressed
        self.warn_bt_pressed = 0    # is Warning ON/OFF button pressed


class Art:

    def __init__(self, config, log, mdf):

        # store config
        self.config = config

        # logging
        self.log = log
        self.mdf = mdf

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

        # PID Controller
        self.pid = PID(config)

        # dict to remember the button states
        self.button_states = {
            'SFB': 0,               # Braking
            'WH_UP': 0,             # lever NOT ok
            'AUS': 0,               # lever OFF
            'WA': 0,                # lever ON/RESUME/+1
            'S_PLUS_B': 0,          # lever UP +10
            'S_MINUS_B': 0,         # lever DOWN -10
            'ART_ABW_BET': 0,       # Button Warning ON/OFF
            'CRASH': 0,             # Crash detection
            'VMAX_AKT': 0,          # Limiter
        }

        self.log.info('INIT ACC - NOT READY')

    # todo LIM and Long press
    def update_input(self, new_msgs, all_data):

        # print(new_msgs)
        # old_signals = self.vehicle_msgs['signals']

        # at fist the system have to be ready
        if self.art.ready:

            # is the driver braking
            if self.is_btn_pressed(new_msgs, 'SFB'):
                self.art_braking()

            # Warning ON/OFF toggle button
            if self.is_btn_pressed(new_msgs, 'ART_ABW_BET'):
                self.art_warning_button()

            # CRASH detected
            if self.is_btn_pressed(new_msgs, 'CRASH'):
                self.log.critial('CRASH detected')
                self.reset_to_default()

            # check if lever is ok
            self.is_btn_pressed(new_msgs, 'WH_UP')

            # LEVER INPUTS
            # lever is ok
            if self.button_states['WH_UP'] == 0:

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

                # Todo Limiter
                """
                if self.is_btn_pressed(new_msgs, 'VMAX_AKT'):
                    self.lim_activatio()
                    
                if self.is_btn_pressed(new_msgs, 'VMAX_AKT', mode=1): # FALLING_EDGE
                    self.lim_deactivatio()
                """

                # todo: long hold button
                # per sec one button trigger

        # update dataset with the newest data
        # self.vehicle_msgs['signals'].update(new_msgs)
        self.vehicle_msgs.update(all_data)

        # do the basic ready check
        self.is_ready()

    # todo Mode holding
    def is_btn_pressed(self, data, signal, mode=0):

        # Modes
        # 0 = Rising Edge - button is now pressed - DEFAULT
        # 1 = Falling Edge - button is not pressed anymore
        # 2 = Holding - Triggers output every x time during long hold
        # Modes not needed now:
        # falling edge, is ON, is OFF

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
                    if self.button_states[signal] == 0:
                        # YES it was not pressed before -> RISING EDGE detected -> action
                        print('RE')
                        out = True

            # MODE 1: Falling Edge - button is not pressed anymore
            if mode == 1:
                # is button NOT pressed now?
                if signal_value == 0:
                    # YES it is pressed now
                    # but was it pressed before?
                    # if self.button_states[signal] == 1:
                    if self.button_states[signal] > 0:  # adaption to handle timestamps in button states
                        # YES it was pressed before -> FALLING EDGE detected -> action
                        print('FE')
                        out = True

            # MODE 2: Holding - Triggers output every x time during long hold
            if mode == 2:
                # is button pressed now
                if signal_value == 1:
                    now = utils.ts_ms()

                    hold_time = 0

                    if self.button_states[signal] > 1:
                        # how long is button already pressed
                        hold_time = now - self.button_states[signal]

                    # is it over the holding time
                    if hold_time >= self.config.lever_hold_time:
                        # reset trigger holding time
                        self.button_states[signal] = now
                        # report
                        print('HO')
                        print(hold_time)
                        out = True

            # remember the current state to compare it with the next input
            state = signal_value
            # set when button was pressed ONYL when the button is pressed, and it was not pressed before
            if signal_value == 1 and self.button_states[signal] == 0:
                # set timestamp
                state = utils.ts_ms()

            # safe current state
            self.button_states[signal] = state

        # report result
        return out

    def art_warning_button(self):
        self.log.info('Warning Button pressed')

        # if ART warning button pressed toggle warning status
        if self.art_msg['ART_ABW_AKT'] == 0:
            self.art_msg['ART_ABW_AKT'] = 1
            self.log.debug('Activate warnings')
        else:
            self.art_msg['ART_ABW_AKT'] = 0
            self.log.debug('Deactivate warnings')

    def art_braking(self):

        self.log.info('BRAKING')

        if self.art.state == ArtState.ACC_active:
            # self.level_off()
            self.acc_deactivation()

            # display trigger
            self.acc_set_dspl_trigger()

    def lever_off(self):
        self.log.info('Lever OFF pressed')

        if self.art.state == ArtState.ACC_active:
            # display trigger
            self.acc_set_dspl_trigger()

            self.acc_deactivation()

        # todo Limiter off

    # level_resume pressed
    def lever_wa(self):
        self.log.info('Lever WA pressed')

        # display trigger
        self.acc_set_dspl_trigger()

        # signal = self.vehicle_msgs['signals']

        # ACC ready -> activation
        if self.art.state == ArtState.ACC:

            # RESUME Speed
            v_set = self.art_msg['V_ART']

            # set speed only if speed was not set before
            if v_set == 0:
                v_set = math.ceil(self.vehicle_msgs['signals']['V_ANZ'])

            # and power
            self.acc_activation(v_set)

        # ACC active
        if self.art.state == ArtState.ACC_active:
            #  speed +1
            self.art_msg['V_ART'] += 1

            # upper limit
            if self.art_msg['V_ART'] > self.config.acc_max_speed:
                self.art_msg['V_ART'] = self.config.acc_max_speed

            self.log.info('ACC: set speed to ' + str(self.art_msg['V_ART']))

    def lever_up(self):
        self.log.info('Lever PLUS pressed')

        # display trigger
        self.acc_set_dspl_trigger()

        # signal = self.vehicle_msgs['signals']

        # ACC ready -> activation
        if self.art.state == ArtState.ACC:

            v_set = math.ceil(self.vehicle_msgs['signals']['V_ANZ'])

            # and power
            self.acc_activation(v_set)

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
        self.log.info('Lever MINUS pressed')

        # display trigger
        self.acc_set_dspl_trigger()

        # signal = self.vehicle_msgs['signals']

        # ACC ready -> activation
        if self.art.state == ArtState.ACC:

            v_set = math.ceil(self.vehicle_msgs['signals']['V_ANZ'])

            # and power
            self.acc_activation(v_set)

        # ACC active
        if self.art.state == ArtState.ACC_active:
            #  flor speed to lower tens -10
            speed = self.art_msg['V_ART'] - 1
            self.art_msg['V_ART'] = math.floor(speed/10)*10

            # lower limit
            if self.art_msg['V_ART'] < self.config.acc_min_speed:
                self.art_msg['V_ART'] = self.config.acc_min_speed

            self.log.info('ACC: set speed to ' + str(self.art_msg['V_ART']))

    def acc_activation(self, target_speed):

        ready_to_activate = True

        target_speed = round(target_speed)

        # activation check

        signal = self.vehicle_msgs['signals']

        # is driver BRAKING currently
        if self.button_states['SFB'] == 1:
            self.log.warning('Cant enable ACC: Driver is braking')

            ready_to_activate = False

        # check for MIN speed
        if signal['V_ANZ'] < int(self.config.acc_min_speed):
            self.log.warning('Cant enable ACC: too slow')
            # trigger '---' display
            self.acc_set_dspl_lim_trigger()
            ready_to_activate = False

        # check for MAX speed
        if signal['V_ANZ'] > int(self.config.acc_max_speed):
            self.log.warning('Cant enable ACC: too fast')
            # trigger '---' display
            self.acc_set_dspl_lim_trigger()
            ready_to_activate = False

        # lever OK
        if signal['WH_UP'] == 1:
            self.log.warning('Cant enable ACC: Selector Level implausible')
            ready_to_activate = False

        # all good -> ACTIVATE ACC
        if ready_to_activate:

            self.log.info('ACC activation')

            # activate ACC
            self.art.state = ArtState.ACC_active

            # set speed
            self.art_msg['V_ART'] = target_speed
            self.log.info('ACC: set speed to ' + str(self.art_msg['V_ART']))

            # display ein
            self.art_msg['ART_SEG_EIN'] = 1

            # init PID Controller
            self.pid.init_pid(target_speed, signal['M_STA'], signal['M_MIN'], signal['M_MAX'])

            # set distance
            self.acc_calc_distance()

        else:
            # just to be sure
            self.art.state = ArtState.ACC

    # todo
    def acc_calc(self):
        # self.log.debug('ACC calc')
        # get signals
        signal = self.vehicle_msgs['signals']

        # set/update V_ZIEL or in radar calc (rounded up)
        # Todo in radar calc
        self.art_msg['V_ZIEL'] = math.ceil(self.art_msg['V_ART'])

        # todo ART_VFBR (VerFügBaR - available)
        # goes off [0] if speed it too slow (trigger dspy), recover [1] after trigger time
        # blocks reactivation if state is 0 ???

        # set default values - will be overwritten if everything is correct
        self.art_msg['ART_REG'] = 0
        self.art_msg['M_ART'] = 0
        self.art_msg['ART_BRE'] = 0
        self.art_msg['MBRE_ART'] = 0
        self.art_msg['BL_UNT'] = 0

        # is ready
        if self.art.ready:

            # ACC is ACTIVE
            if self.art.state == ArtState.ACC_active:

                # double check braking
                if signal['SFB'] == 1:
                    # switch off - driver is breaking
                    self.acc_deactivation()
                    return

                # min speed limit
                if signal['V_ANZ'] < self.config.acc_min_speed:
                    # switch off if car is too slow
                    self.acc_deactivation()
                    return

                # ART overwrite by driver
                # ART_UBERSP
                # M_FV (Fahrervorgabe) is bigger then the M_MIN (in case of decelerating) AND
                # M_FV is 15Nm bigger the ACC Moment
                if signal['M_FV'] > (self.art_msg['M_ART'] + 15) \
                        and signal['M_FV'] > signal['M_MIN'] \
                        and self.art_msg['ART_REG'] == 1:
                    # if was not overwriten before
                    if self.art_msg['ART_UEBERSP'] == 0:
                        self.log.info('Overwrite active')
                    # is overwriten now
                    self.art_msg['ART_UEBERSP'] = 1
                else:
                    # if it was overwriten before
                    if self.art_msg['ART_UEBERSP'] == 1:
                        self.log.info('Overwrite deactive')
                    # it's not overwriten now
                    self.art_msg['ART_UEBERSP'] = 0

                # DO YOUR MAGIC PID-CONTROLLER
                torque_request = self.pid.pid_calc(signal['V_ANZ'], self.art_msg['ART_UEBERSP'])

                # min M_ART is 160 Nm
                M_ART = max(torque_request, 160)

                # invert BRAKE Torque and cap at 0
                MBRE_ART = min(torque_request, 0) * -1

                # set acceleration moment
                self.art_msg['M_ART'] = M_ART

                # enable ART_REG acceleration
                if self.config.art_reg_enabled == True:

                    self.art_msg['ART_REG'] = 1

                # BRAKING is on and its NOT OVERWRITEN BY DRIVER
                if MBRE_ART > 0 and self.art_msg['ART_UEBERSP'] == 0:

                    # enable ART_BRE deceleration / braking
                    if self.config.art_bre_enabled == True:
                        # enable ART BRAKES
                        self.art_msg['ART_BRE'] = 1
                        # set BRAKE troque
                        self.art_msg['MBRE_ART'] = MBRE_ART

                    # todo Braklight suppression details. by deceleration or brake torque?
                    # between 0 and 15Nm
                    if MBRE_ART <= 15:
                        self.art_msg['BL_UNT'] = 1

                # Todo
                # ART channels
                # MPAR_ART - parity bit at changes - is always 0 ???

                # GMIN_ART
                # GMAX_ART
                # SLV_ART
                # AKT_R_ART - active downshift request
                # DYN_UNT

        # AAS_LED_BL ??? always 0
        # ART_REAKT ??? always 0

        # ART_ERROR 4 - External Error

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

    # disable the acc and reset outputs
    def acc_deactivation(self):

        # disable segment display
        self.art_msg['ART_SEG_EIN'] = 0

        self.log.info('ACC deactivation')

        # reset outputs
        self.art_msg['ART_REG'] = 0
        self.art_msg['M_ART'] = 0
        self.art_msg['ART_BRE'] = 0
        self.art_msg['MBRE_ART'] = 0
        self.art_msg['BL_UNT'] = 0

        # switch to state ACC ready
        # todo: switch state here or in caller function?
        self.art.state = ArtState.ACC

        # display trigger
        # self.acc_set_dspl_trigger()

    # todo calc warnings only with radar input
    def acc_calc_warnings(self):
        # todo car too close
        # todo delta speed too big
        # ART_INFO -> Light
        # ART_WT -> Warning (Ton) Sound
        # AAS_LED_BL -> LED ACC blinking -> check/test
        pass

    # todo
    def radar(self):
        # Data
        # S_OBJ - standing object detected
        # ABST_R_OBJ - distance to relevant object [m]
        # OBJ_ERK - object detected
        # V_ZIEL - target vehicle speed [kph]
        # OBJ_AGB - Object offer acc ? -> check
        # ART_REAKT - show reaktivation after error -> check/test
        pass

    # todo
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
        self.log.debug('Trigger Display')

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
        # set VERUGBAR
        self.art_msg['ART_VFBR'] = 0

    def acc_reset_trigger(self):
        # reset only if a trigger is active
        if self.art.dspl_trigger_ts != 0:

            # get current time
            now = utils.ts_ms()

            # to calc time delta
            delta_time = now - self.art.dspl_trigger_ts

            # time is up
            if delta_time >= self.config.art_trigger_time:
                self.log.debug('Reset Display trigger')

                # clear
                self.art_msg['ART_DSPL_EIN'] = 0
                self.art_msg['ART_DSPL_LIM'] = 0
                self.art_msg['ART_DSPL_BL'] = 0
                # is ready again
                self.art_msg['ART_VFBR'] = 1
                # clear trigger
                self.art.dspl_trigger_ts = 0

    # 10 hz tricked tick for calc update
    def tick_10hz(self):
        # 10Hz timed
        # to requestes can output

        self.log.debug('10Hz tick')

        # basic ready check also after some time
        self.is_ready()

        # TM_EIN_ART - ART is ready
        if self.art.ready:
            self.art_msg['TM_EIN_ART'] = 1
        else:
            self.art_msg['TM_EIN_ART'] = 0

        # update safety distance
        self.acc_calc_distance()

        # general warnings
        self.acc_calc_warnings()

        if self.art.ready:
            # do the magic
            self.acc_calc()
            # todo self.lim_calc()
        else:
            # todo reset
            pass

        # increment can msg counter (BZ - BotschaftsZähler 0-15)
        self.update_bz()

        # safe signals to MDF
        self.signal_log()

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

        # load DEFAULT values
        self.art_msg = self.art_default_msg.copy()

        # but remember target speed ;)
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
        # todo centralize this list
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

    def status_log(self):
        # write status to log
        # self.log.info(f"ART {self.art.state} \tV_Target: {self.art_msg['V_ART']}")
        return {
            **self.art_msg,
            'ready': self.art.ready,
            'state': self.art.state,
        }

    def signal_log(self):
        # writes signals to MDF log file
        self.mdf.add_signal('art_ready', self.art.ready)
        self.mdf.add_signal('art_state', self.art.state.value)

        # pid signals
        self.mdf.add_signal('pid_integral', self.pid.integral)
        self.mdf.add_signal('pid_acceleration', self.pid.acceleration)
        self.mdf.add_signal('pid_set_speed', self.pid.set_speed)
# end class ART
