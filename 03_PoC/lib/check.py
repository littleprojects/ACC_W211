
"""
Function library for Checks

"""
from lib import utils

# ready check
def is_acc_ready(vehicle_msg, log):
    """
    This function checks the CAN msgs and signals if everything is ok
    """

    #global vehicle_msg
    #global log

    ts_now = utils.ts_ms()

    # all MSG id there they need to check
    needed_msg_id_list = [
        # mandatory msgs
        '0x200',    # BS (Break System) - drive direction, ESP
        '0x300',    # BS - enable ART
        '0x236',    # ART_LRW - Steering
        '0x238',    # ART_MRM - Buttons
        '0x240',    # EZS - Buttons
        '0x212',    # MS - Enable ART
        '0x308',    # MS - Data
        '0x312',    # MS - Moments
        '0x412',    # Kombi - speed
        # other msgs
        '0x408',    # Kombi
        '0x328',    # BS
        '0x218',    # GS - Gearbox System
        '0x418',    # GS
        '0x210',    # MS (Motor System) - Pedal
        '0x608',    # MS
        '0x328',    # BS
    ]

    all_msgs_found = True

    for msg_id in needed_msg_id_list:
        if not (msg_id in vehicle_msg['msgs']):
            all_msgs_found = False

            log.debug('Checker: ID ' + msg_id + ' not found')

            # stop loop
            break

    if not all_msgs_found:
        log.debug('Chekcer: Msgs incomplete')
        return False

    # no MSG ts is to old

    all_msg_in_time = True

    max_delay = 500 # ms

    for msg_id in needed_msg_id_list:
        ts_last_msg = vehicle_msg['msgs'][msg_id]

        # delay in ms
        delay = ts_last_msg - ts_now

        if delay > max_delay:

            all_msg_in_time = False

            log.debug('Checker: ' + msg_id + ' is to old - ' + str(delay) + ' ms')

            # end loop
            break

    if not all_msg_in_time:
        log.warning('Checker: Msgs to old')
        return False

    # needed Signals are in range

    signal = vehicle_msg['signals']

    if (
        # break by driver
        signal['SFB'] == 1

        # speed > 30
        #or signal['V_ANZ'] >= 30.0
        # SBC S/H not active
        or signal['SBCSH_AKT'] == 1
        # check for Reverse driving 0 Stop; 1 Forward; 2 reverse
        or signal['DRTGTM'] == 2
        # BS 200
        # EPS
        or signal['ESP_KL'] == 1
        or signal['ESP_INFO_DL'] == 1
        or signal['ESP_INFO_BL'] == 1
        # ABS
        or signal['ABS_KL'] == 1
        or signal['BRE_KL'] == 1
        # BS_300 Enabel ART
        or signal['ART_E'] == 1
        # ESZ_240
        or signal['ART_VH'] == 0
        # MS210 Notlauf
        or signal['NOTL'] == 1
        # MS 308
        or signal['OEL_KL'] == 1
        or signal['UEHITZ'] == 1
        or signal['TEMP_KL'] == 1
            ):
        return False

    #

    return True

def enable_acc(vehicle_msg, log):

    signal = vehicle_msg['signals']

    # not Wahlhebel unplausibel speed > 30
    if signal['WH_UP'] == 0 and signal['V_ANZ'] >= 30.0:
        if (
            # ART_MRM 238
            # Wiederaufnahme
            signal['WA'] == 1
            or signal['S_PLUS_B'] == 1
            or signal['S_MINUS_B'] == 1
                ):
            return True

    return False


def disable_acc(vehicle_msgs, log):

    signal = vehicle_msgs['signals']

    # disable at Driver Brakes or Switch of
    if signal['SFB'] == 1 or signal['AUS'] == 1:
        return True

    return False
