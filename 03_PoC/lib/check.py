
"""
Function library for Checks

"""
from lib import untils

# ready check
def is_acc_ready():
    """
    This function checks the CAN msgs and signals if everything is ok
    """

    global vehicle_msg
    global log

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
        if not msg_id in vehicle_msg['msg_ts']:
            all_msgs_found = False

            log.debug('Checker: ID ' + msg_id + ' not found')

            # stop loop
            break

    if not all_msgs_found:
        log.warning('Chekcer: Msgs incomplete')
        return False

    # no MSG ts is to old

    all_msg_in_time = True

    max_delay = config['check_msg_delay']

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

    return True


