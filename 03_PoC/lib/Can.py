import can
import cantools
import queue

#from Config import Config
#from Logger import Logger
from time import sleep


class Can:
    """
    Connecting to the can and send messages
    """

    def __init__(self, interface, channel, bitrate, log, retry_in_sec='5', is_extended=False, filter=None):

        self.log = log

        """ Bus """
        self.bus = None

        """ Connection """
        self.interface = interface
        self.channel = channel
        #self.app_name =
        self.bitrate = int(bitrate)
        self.retry_in_seconds = int(retry_in_sec)
        self.is_extended_id = int(is_extended)

        """ Filter """
        self.filter = filter

        """ Index to check if we should log the receive message """
        self.index = 0

    def connect(self):
        """
        trying to connect to the can
        :return:
        """
        self.log.info(f"CAN_{self.channel}: Connecting to can")
        try:
            """ Connecting to the can. Its possible to change all values in the .conf file """
            self.bus = can.interface.Bus(interface=self.interface, channel=self.channel, bitrate=self.bitrate, app_name='NewApp')

            # add filter
            try:
                if self.filter is not None:
                    self.bus.set_filters(self.filter)
            except Exception as e:
                self.log.warning(f"CAN_{self.channel}: Cant set Filter" + str(e))

            return self.bus

        except Exception as e:
            """ If it's not possible to connect, print a message to the log """
            self.log.error(f"CAN_{self.channel}: Connection failed" + str(e) + ' --- retry')
            #self.log.error(e)

            #self.bus.shutdown()
            self.shutdown_connection()

            """ Try it again in some seconds """
            self.log.debug(f"CAN_{self.channel}: Trying again in {self.retry_in_seconds} seconds")
            sleep(self.retry_in_seconds)
            self.get_connection()

    def shutdown_connection(self):
        """
        shutting down the connection
        disconnect before we want to connect to the can. Otherwise, we would get an error
        :return:
        """
        self.log.debug(f"CAN_{self.channel}: Shutting down the connection")
        try:
            if self.bus is not None:
                """ Shutting down the connection """
                self.bus.shutdown()
        except Exception as e:
            """ If that is not possible, print it to the log """
            self.log.debug(f"CAN_{self.channel}: Shutting down the connection is not possible")
            self.log.error(e)

    def wait_for_new_message(self):
        """ Checking for new parsers. If there are any in the queue, start creating the can messages """
        self.log.info("CAN_{self.channel}: Starting the can messenger")

        while True:
            try:
                sleep(0.001)
                while not self.parser_queue.empty():
                    self.create_messages(self.parser_queue.get())
            except Exception as e:
                self.log.error(e)

    def send_message(self, data, arbitration_id):
        """
        send a can message
        :return:
        """
        """ Creating the can message. The arbitration_id is the id the can messages has. If you wanna find out the id of a can message, 
        open the database in CANdb++ """
        msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=self.is_extended_id)

        try:
            """ Sending the can message """
            self.bus.send(msg)
            """ We are not printing every message to the log """
            if self.index % self.print_logger == 0:
                self.log.info(f"CAN_{self.channel}: Message send: {msg}")
            else:
                self.log.debug(f"CAN_{self.channel}: Message send: {msg}")
            self.index += 1
        except Exception as e:
            self.log.debug(f"CAN_{self.channel}: Could not send the message")
            self.log.error(e)

