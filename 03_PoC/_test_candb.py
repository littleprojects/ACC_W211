import cantools
from lib import utils

from asammdf import MDF, Signal

from pprint import pprint
db = cantools.database.load_file('CAN_C.dbc')
db.messages

print(db.messages)
print()

message = db.get_message_by_name('MS_210h')

print(message)
print(hex(message.frame_id))
print(message.signals)
print(message.signal_tree)
print(message.signals[0])
print()

print(utils.dbc_signal(db, 'Pedalwert').comments[None])


sig = Signal(samples=[0], timestamps=[0], name='test', unit='test')
#sig.unit = 'test'

print(sig)
