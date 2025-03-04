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

    def __init__(self, interface, channel, bitrate, dbc, log, retry_in_sec='5', is_extended=False, filter=None):

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

        """ Database """
        self.db = self.get_database(dbc)

        """ Parser """
        self.parser = None
        self.parser_queue = queue.Queue()

        """ Filter """
        self.filter = filter

        """ Index to check if we should log the receive message """
        self.index = 0

    def set_parser(self, parser):
        """ Setting the parser. We need the parser to store already decoded messages """
        self.log.debug(f"CAN_{self.channel}: Setting the parser: {parser}")
        self.parser = parser

    def add_to_parser_queue(self, parser):
        """ Adding a new parser to the queue, so we don't skip one """
        self.log.debug(f"CAN_{self.channel}: adding a new parser to the queue: {parser}")
        self.parser_queue.put(parser)

    def get_database(self, dbc):
        """ Getting the database path from the .conf file """
        database_path = dbc

        self.log.info(f"CAN_{self.channel}: Connecting to database: {database_path}")

        try:
            """ Trying to connect to the database """
            return cantools.database.load_file(database_path)
        except Exception as e:
            self.log.critical("CAN_{self.channel}: Failed to connect to database: " + dbc)
            self.log.error(e)
            exit()

    def get_connection(self):
        """
        trying to connect to the can
        :return:
        """
        self.log.info(f"CAN_{self.channel}: Connecting to can")
        try:
            """ Connecting to the can. Its possible to change all values in the .conf file """
            self.bus = can.interface.Bus(interface=self.interface, channel=self.channel, bitrate=self.bitrate)

            # add filter
            try:
                if self.filter is not None:
                    self.bus.set_filters(self.filter)
            except Exception as e:
                self.log.warning(f"CAN_{self.channel}: Cant set Filter" + str(e))
                
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

    def receive_message(self):
        """ We don't need this function at the moment. But with this function its possible to receive messages from the can """
        try:
            self.log.debug(f"CAN_{self.channel}: Received message {self.bus.recv()}")
        except Exception as e:
            self.log.debug(f"CAN_{self.channel}: Receiving message was not possible")
            self.log.error(e)

    def create_messages(self, parser):
        """ Checking which parser needs which can messages. You can change that f.e. in BESTPOS.py """
        for can_message in parser.can_messages:
            exec(f"self.create_message(self.{can_message})")

    def create_message(self, function):
        try:
            """ Executing the message we want to create """
            message, data = function()

            """ Sending the can message with the id and the data """
            self.logger.debug(f"CAN_{self.channel}: Sending can message: {data}")
            self.send_message(data, message.frame_id)

            # self.receive_message()
        except Exception as e:
            self.logger.debug("CAN_{self.channel}: Missing attribute")
            self.logger.debug(e)