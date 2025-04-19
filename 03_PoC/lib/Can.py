import can
# import cantools
# import queue

# from Config import Config
# from Logger import Logger
from time import sleep


class Can:
    """
    Connecting to the can and send messages
    """

    def __init__(self, interface, channel, bitrate, log, app_name='',
                 retry_in_sec='5', is_extended=False, filter_list=None):

        self.log = log

        self.print_logger = 1000

        # bus
        self.bus = None

        # connection
        self.interface = interface
        self.channel = channel
        self.app_name = app_name
        self.bitrate = int(bitrate)
        self.retry_in_seconds = int(retry_in_sec)
        self.is_extended_id = is_extended

        # Filter
        self.filter = filter_list

        # Index to check if we should log the received message
        self.index = 0

    def connect(self):
        """
        trying to connect to the can
        :return:
        """
        self.log.info(f"CAN_{self.channel}: Connecting to can")
        try:
            """ Connecting to the can. Its possible to change all values in the .conf file """
            self.bus = can.interface.Bus(interface=self.interface,
                                         channel=self.channel,
                                         bitrate=self.bitrate,
                                         app_name=self.app_name
                                         )

            self.set_filter(self.filter)

            return self.bus

        except Exception as e:
            """ If it's not possible to connect, print a message to the log """
            self.log.error(f"CAN_{self.channel}: Connection failed" + str(e) + ' --- retry')
            # self.log.error(e)

            # try shutdown
            self.shutdown_connection()

            """ Try it again in some seconds """
            self.log.debug(f"CAN_{self.channel}: Trying again in {self.retry_in_seconds} seconds")
            sleep(self.retry_in_seconds)
            self.connect()

    def set_filter(self, filter_list):

        # Todo: create a Filter list to reduce loads

        try:
            if filter_list is not None:

                #filter = []
                # [{"can_id": 0x11, "can_mask": 0x21, "extended": False},
                # {"can_id": 0x11, "can_mask": 0x21, "extended": True},]

                # create filter list
                #for id in filter_list:
                #    filter.append({"can_id": id, "can_mask": 0x7FF, "extended": False})

                # add filter
                self.log.debug('Set Filter: ' + str(filter_list))

                self.bus.set_filters(filter_list)
        except Exception as e:
            self.log.warning(f"CAN_{self.channel}: Cant set Filter" + str(e))

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

    def loop(self, q_in, q_out, flag_new_msg, stop_event):

        while True:

            # SEND CAN Msg

            # send ONE can msg in queue -> delays out a bit
            # if not q_out.empty():

            # send ALL CAN in queue -> block receiving more
            while not q_out.empty():
                # read msg from queue
                msg_data = q_out.get()
                # create can msg
                msg = can.Message(arbitration_id=msg_data['id'],
                                  data=msg_data['data'],
                                  is_extended_id=False
                                  )
                # send msg
                self.bus.send(msg)

                # debug output
                if self.index % self.print_logger == 0:
                    self.log.info(f"CAN_{self.channel}: Message send: {self.index}")

                self.index += 1

            # THEN

            # READ CAN Msg
            # wait for can msg with timeout
            msg = self.bus.recv(0.01)   # 0.01 = 100Hz

            if msg:
                q_in.put(msg)

                # set new msg flag
                flag_new_msg.set()

            # break loop at stop event
            if stop_event.is_set():
                break

    """ 
    # not in use -> is done in CAN_handler
    def wait_for_new_message(self):
        # Checking for new parsers. If there are any in the queue, start creating the can messages
        self.log.info("CAN_{self.channel}: Starting the can messenger")

        while True:
            try:
                sleep(0.001)
                while not self.parser_queue.empty():
                    self.create_messages(self.parser_queue.get())
            except Exception as e:
                self.log.error(e)
    """

    """
    # not in use -> is done in loop function
    def send_message(self, data, arbitration_id):

        # Creating the can message. The arbitration_id is the id the can messages has.
        msg = can.Message(is_extended_id=False, arbitration_id=arbitration_id, data=data)

        try:
            # Sending the can message
            self.bus.send(msg)
            # We are not printing every message to the log 
            if self.index % self.print_logger == 0:
                self.log.info(f"CAN_{self.channel}: Message send: {msg}")
            else:
                self.log.debug(f"CAN_{self.channel}: Message send: {msg}")
            self.index += 1
        except Exception as e:
            self.log.debug(f"CAN_{self.channel}: Could not send the message")
            self.log.error(e)
    """
