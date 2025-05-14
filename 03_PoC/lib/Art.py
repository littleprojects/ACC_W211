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
        #self.braking = 0            # is driver braking
        #self.lever_wa_pressed = 0   # is WA pressed
        #self.lever_up_pressed = 0   # is UP pressed
        #self.lever_dw_pressed = 0   # is DOWN pressed
        #self.lever_off_pressed = 0  # is OFF pressed
        #self.level_lim_pressed = 0  # is LIMITER pressed
        #self.warn_bt_pressed = 0    # is Warning ON/OFF button pressed


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

        self.ready_error = 0

        self.speed_mps = 0  # [m/s]
        self.long_acceleration = 0
        self.lat_acceleration = 0
        self.corner_radius = 0       # 0 = absolute straight

        self.info_light_duration = 0
        self.warn_beep_duration = 0

        # delta timestamp
        self.last_ts = utils.ts_ms()
        self.dt_ms = 0

        # last data
        self.last_speed = 0
        self.last_speed_ts = utils.ts_ms()
        self.dt_speed = 0

        self.log.info('INIT ACC - NOT READY')

    # todo LIM
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

        # update speed only if an update is available
        if 'V_ANZ' in new_msgs:
            current_speed = new_msgs['V_ANZ']

            if 'V_ANZ' in self.vehicle_msgs['signals']:
                #old_speed = self.vehicle_msgs['signals']['V_ANZ']

                self.calc_acceleration(current_speed, self.last_speed)

            self.last_speed = current_speed

        # update dataset with the newest data
        # self.vehicle_msgs['signals'].update(new_msgs)
        self.vehicle_msgs.update(all_data)

        # do the basic ready check
        # self.is_ready()
        # is done at the 1o Hz tick to reduce load

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
                        self.log.debug('Button: ' + signal + ' - Rising Edge detection')
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
                        self.log.debug('Button: ' + signal + ' - Falling Edge detection')
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
                        self.log.debug('Button: ' + signal + ' - Hold detection - ' + str(hold_time) + 'ms')
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

    def calc_acceleration(self, current_speed, last_speed):
        # current timestamp
        now_ts = utils.ts_ms()

        # delta time in ms; 100 = 10Hz
        dt = (now_ts - self.last_speed_ts) / 1000

        # calc acceleration
        delta_speed = current_speed - last_speed
        delta_speed_mps = delta_speed / 3.6  # kph to m/s

        # speed in m/s
        self.speed_mps = round(current_speed / 3.6, 2)  # kph to m/s

        # should not be zero and lower than 1 sec
        if 0 < dt < 1:
            # a = m/s /s
            long_acc = delta_speed_mps / dt  #

            self.long_acceleration = round(long_acc, 2)
        else:
            self.log.warning('ACC CALC: dt out ov scope: ' + str(dt))
            self.long_acceleration = 0

        # safe values
        self.last_speed_ts = now_ts
        self.dt_speed = dt
        self.last_speed = current_speed
        # print(str(current_speed) + ' - ' + str(last_speed) + ' = ' + str(delta_speed) + ' -> ' + str(self.long_acceleration))

    # Todo calc lat (side) acceleration
    def calc_lat_acceleration(self):

        current_rotation = self.vehicle_msgs['signals']['GIER_ROH']

        # Radius R = speed in m/s * angular velocity (rad/s) = v * ψ
        # Todo is it in RAD or DEG???
        r = self.speed_mps * current_rotation * 0.0174533   # = math.pi/180 for Deg to RAD

        if r > 0:
            # a_lat = speed^2 / radius
            a_lat = self.speed_mps ** self.speed_mps / r
        else:
            a_lat = 0

        self.lat_acceleration = round(a_lat, 2)
        self.corner_radius = round(r, 1)

    def acc_activation(self, target_speed):

        ready_to_activate = True

        target_speed = round(target_speed)

        # activation check

        signal = self.vehicle_msgs['signals']

        # is driver BRAKING currently
        if self.button_states['SFB'] == 1:
            self.log.warning('Cant enable ACC: Driver is braking - SFB = 1')

            ready_to_activate = False

        # check for MIN speed
        if signal['V_ANZ'] < int(self.config.acc_min_speed):
            self.log.warning('Cant enable ACC: too slow - V_ANZ: ' + str(signal['V_ANZ']))
            # trigger '---' display
            self.acc_set_dspl_lim_trigger()
            ready_to_activate = False

        # check for MAX speed
        if signal['V_ANZ'] > int(self.config.acc_max_speed):
            self.log.warning('Cant enable ACC: too fast - V_ANZ: ' + str(signal['V_ANZ']))
            # trigger '---' display
            self.acc_set_dspl_lim_trigger()
            ready_to_activate = False

        # lever OK
        if signal['WH_UP'] == 1:
            self.log.warning('Cant enable ACC: Selector Level implausible - WH_UP = 1')
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

    # todo Adaptive Cruise Control calc
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

            # ACC is ACTIVE - safety checks
            if self.art.state == ArtState.ACC_active:

                # double check braking
                if signal['SFB'] == 1:
                    # switch off - driver is braking
                    self.log.info('Driver brakes - deactivation - SFB = 1')
                    self.acc_deactivation()
                    # return

                # min speed limit
                if signal['V_ANZ'] < self.config.acc_min_speed:
                    # switch off if car is too slow
                    self.log.warning('Too slow - deactivation - V_ANZ < acc_min_speed = ' +
                                     str(signal['V_ANZ']) + ' < ' + str(self.config.acc_min_speed))

                    # beep
                    self.set_warning(beep=1, duration=self.config.warning_time)

                    # acc off
                    self.acc_deactivation()
                    # return

                # OFF by too much acceleration
                if self.long_acceleration >= self.config.acc_off_acc:
                    self.log.warning('Too much acceleration - deactivation - long_acc >= acc_off_acc ' +
                                     str(self.long_acceleration) + ' m/s² >= ' + str(self.config.acc_off_acc))

                    # beep
                    self.set_warning(beep=1, duration=self.config.warning_time)

                    # acc off
                    # Todo - check and enable
                    # self.acc_deactivation()

                # OFF by too much deceleration
                if -self.long_acceleration >= self.config.acc_off_dec:
                    self.log.warning('Too much deceleration - deactivation - long_dec >= acc_off_dec ' +
                                     str(-self.long_acceleration) + ' m/s² >= ' + str(self.config.acc_off_acc))

                    # beep
                    self.set_warning(beep=1, duration=self.config.warning_time)

                    # acc off
                    # Todo - check and enable
                    # self.acc_deactivation()

                """ Todo - lat acceleration calc is wrong
                # OFF by too fast cornering
                if abs(self.lat_acceleration) >= self.config.acc_off_lat_acc:
                    self.log.warning('Too much (corner) lat acc - deactivation - lat_acc >= acc_off_lat_acc ' +
                                     str(abs(self.lat_acceleration)) + ' m/s² >= ' + str(self.config.acc_off_lat_acc))

                    # beep
                    self.set_warning(beep=1, duration=self.config.warning_time)

                    # acc off
                    # Todo - check and enable
                    # self.acc_deactivation()
                """

            # ACC is ACTIVE - after safety checks
            if self.art.state == ArtState.ACC_active:

                # ART overwrite by driver
                # ART_UBERSP
                # M_FV (Fahrervorgabe) is bigger then the M_MIN (in case of decelerating) AND
                # M_FV is xNm bigger the ACC Moment
                if signal['M_FV'] > (self.art_msg['M_ART'] + self.config.acc_pause_nm_delta) \
                        and signal['M_FV'] > signal['M_MIN']:
                        # and self.art_msg['ART_REG'] == 1\

                    # if was not overwriten before
                    if self.art_msg['ART_UEBERSP'] == 0:
                        self.log.info('OVERWRITE active by driver')

                    # then it's overwritten now
                    self.art_msg['ART_UEBERSP'] = 1

                    # OVERWRITE / PAUSE at high lateral acceleration (corner speed)
                    """
                    elif abs(self.lat_acceleration) >= self.config.acc_pause_lat_acc:
                            #and self.art_msg['ART_REG'] == 1:
    
                        # if was not overwritten before
                        if self.art_msg['ART_UEBERSP'] == 0:
                            self.log.info('OVERWRITE active by corner speed')
    
                        # is overwritten now
                        self.art_msg['ART_UEBERSP'] = 1
                    """

                # no overwrite active
                else:
                    # if it was overwriten before
                    if self.art_msg['ART_UEBERSP'] == 1:
                        self.log.info('Overwrite off')

                    # it's not overwriten now
                    self.art_msg['ART_UEBERSP'] = 0

                # DO YOUR MAGIC PID-CONTROLLER
                torque_request = self.pid.pid_calc(signal['V_ANZ'],             # current_speed
                                                   self.art_msg['V_ZIEL'],      # set_speed
                                                   self.art_msg['ART_UEBERSP'],  # overwrite
                                                   signal['M_FV'],              # driver moment
                                                   signal['M_MIN'],             # min moment
                                                   signal['M_MAX']              # max moment
                                                   )

                # min M_ART is 160 Nm
                M_ART = max(torque_request, 160)

                # eliminate the toque "dead zone" between 0 to 160 Nm
                if torque_request < 160:
                    torque_request -= 160

                # invert BRAKE Torque and cap at 0
                MBRE_ART = min(-torque_request, 0)

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

    def set_warning(self, light=0, beep=0, duration=200):

        # switch to acc display
        self.acc_set_dspl_trigger()

        if light > 0:
            # set light on timer
            self.info_light_duration = duration

        if beep > 0:
            # set beep on timer
            self.warn_beep_duration = duration

    # todo calc warnings only with radar input
    def warnings(self):
        # todo car too close
        # todo delta speed too big

        # AAS_LED_BL -> LED ACC blinking -> check/test

        # ART_INFO -> Light
        if self.info_light_duration > 0:
            # switch warning light on
            self.art_msg['ART_INFO'] = 1

            # reduce duration time
            self.info_light_duration -= self.dt_ms

            # set to zero if it goes too far
            if self.info_light_duration < 0:
                self.info_light_duration = 0

        else:
            # set warning light off
            self.art_msg['ART_INFO'] = 0

        # ART_WT -> Warning (Ton) Sound
        if self.warn_beep_duration > 0:
            # warning beep on
            self.art_msg['ART_WT'] = 1

            # reduce duration time
            self.warn_beep_duration -= self.dt_ms

            # set to zero if it goes too far
            if self.warn_beep_duration < 0:
                self.warn_beep_duration = 0
        else:
            # warning beep off
            self.art_msg['ART_WT'] = 0

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
            # but doesnt matter if no radar is connected
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

        if self.art.ready:
            # TM_EIN_ART - ART is ready
            # self.art_msg['TM_EIN_ART'] = 1

            # clean inputs
            self.vehicle_msgs['signals']['V_ANZ'] = round(self.vehicle_msgs['signals']['V_ANZ'], 1)

            # calc long and lat (side) acceleration
            self.calc_lat_acceleration()

            # update safety distance
            self.acc_calc_distance()

            # DO THE MAGIC
            self.acc_calc()
            # todo self.lim_calc()

            # general warnings
            self.warnings()
        else:
            # TM_EIN_ART - ART is NOT ready
            # self.art_msg['TM_EIN_ART'] = 0
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

            # if no chancel condition quit - we a are ready to go
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

            self.ready_error = 1
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

            self.ready_error = 2
            return False

        # Todo: check if signals are in range
        # signals = self.vehicle_msgs['signals']

        # Gear is in D
        if 'DRTGTM' in self.vehicle_msgs['signals']:
            if self.vehicle_msgs['signals']['DRTGTM'] != 1:
                if self.art.ready:
                    self.art.ready = False
                    # load default output values
                    self.reset_to_default()
                    self.log.info('Checker: Gear is NOT in D')
                self.ready_error = 3
                return False
        else:
            # Dataset incomplete
            self.ready_error = 4
            return False

        """
        # is SBC Hold active
        if 'SBCSH_AKT' in self.vehicle_msgs['signals']:
            if self.vehicle_msgs['signals']['SBCSH_AKT'] == 1:
                if self.art.ready:
                    self.art.ready = False
                    # load default output values
                    self.reset_to_default()
                    self.log.info('Checker: SBCSH is active')
                self.ready_error = 5
                return False
        else:
            # Dataset incomplete
            self.ready_error = 6
            return False
        """

        # set ready values
        self.set_art_ready()

        self.ready_error = 0

        return True

    def status_log(self):
        # write status to log
        # self.log.info(f"ART {self.art.state} \tV_Target: {self.art_msg['V_ART']}")
        return {
            **self.art_msg,
            'ready': self.art.ready,
            'state': self.art.state,
            'ready_error': self.ready_error
        }

    def signal_log(self):
        # writes signals to MDF log file
        self.mdf.add_signal('art_ready', self.art.ready)
        self.mdf.add_signal('art_state', self.art.state.value)

        # add values
        self.mdf.add_signal('art_dt', self.dt_speed, unit='sec')
        self.mdf.add_signal('art_last_ts', self.last_ts, unit='ms')
        self.mdf.add_signal('art_speed_ms', self.speed_mps, unit='m/s')
        self.mdf.add_signal('art_last_speed', self.last_speed, unit='km/h')
        self.mdf.add_signal('art_acc_long', self.long_acceleration, unit='m/s²')
        self.mdf.add_signal('art_acc_lat', self.lat_acceleration, unit='m/s²')
        self.mdf.add_signal('art_corner_radius', self.corner_radius, unit='m')
        self.mdf.add_signal('art_info_light_duration', self.info_light_duration, unit='ms')
        self.mdf.add_signal('art_warn_beep_duration', self.warn_beep_duration, unit='ms')
        self.mdf.add_signal('art_ready_error', self.ready_error)

        # pid signals
        self.mdf.add_signal('pid_P', self.pid.P)
        self.mdf.add_signal('pid_I', self.pid.I)
        self.mdf.add_signal('pid_D', self.pid.D)
        self.mdf.add_signal('pid_integral', self.pid.integral)
        self.mdf.add_signal('pid_acceleration', self.pid.acceleration, unit='m/s')
        self.mdf.add_signal('pid_set_speed', self.pid.set_speed, unit='km/h')
        self.mdf.add_signal('pid_m_min', self.pid.m_min, unit='Nm')
        self.mdf.add_signal('pid_m_max', self.pid.m_max, unit='Nm')
        self.mdf.add_signal('pid_output', self.pid.old_output, unit='Nm')

        # CAN data sre logged by the CAN_handler
# end class ART
