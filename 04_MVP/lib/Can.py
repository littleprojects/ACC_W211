import time
import can

from lib import Logger
from queue import Queue
from threading import Event
from typing import Optional, Dict, Any


class Can:
    """
    CAN interface wrapper to send and receive messages.
    Messages are exchanged via queues for use in other threads.

    Note: extended_id not implemented
    """

    def __init__(
        self,
        can_config,
        #interface: str,
        #channel: str,
        #bitrate: int,
        #log,
        #app_name: str,
        stop_event: Event,
        retry_in_sec: int = 5,
        filter_list: Optional[list] = None,
    ):
        
        self.cc = can_config
        self.bus: Optional[can.BusABC] = None

        # Connection parameters
        self.interface = self.cc.interface
        self.channel = self.cc.channel
        self.app_name = self.cc.app_name
        self.bitrate = int(self.cc.bitrate)
        
        self.stop_event = stop_event        
        self.retry_in_seconds = int(retry_in_sec)

        # Filters
        self.filter_list = filter_list

        # Counter for sent messages
        self.sent_count = 0

        # Logger
        self.log = Logger.Log('CAN_'+self.channel, config=can_config).get_logger()

    def connect(self) -> Optional[can.BusABC]:
        """
        Try to connect to the CAN bus. Retries until successful.
        """
        self.log.info(f"Connecting to CAN")
        try:
            self.bus = can.interface.Bus(
                interface=self.interface,
                channel=self.channel,
                bitrate=self.bitrate,
                app_name=self.app_name,
            )
            self.set_filter(self.filter_list)
            return self.bus
        except Exception as e:
            self.log.error(f" Connection failed: {e} --- retry")
            self.shutdown_connection()
            self.log.debug(f" Retrying in {self.retry_in_seconds} seconds")
            time.sleep(self.retry_in_seconds)
            return self.connect()

    def set_filter(self, filter_list: Optional[list]) -> None:
        """
        Apply CAN filters to reduce load.
        """
        if not self.bus or not filter_list:
            return
        try:
            self.log.debug(f"Setting filters {filter_list}")
            self.bus.set_filters(filter_list)
        except Exception as e:
            self.log.warning(f"Cannot set filters: {e}")

    def shutdown_connection(self) -> None:
        """
        Shut down the CAN bus connection.
        """
        self.log.debug(f"Shutting down connection")
        if self.bus:
            try:
                self.bus.shutdown()
            except Exception as e:
                self.log.error(f"Shutdown failed: {e}")

    def send_message(self, msg_data: Dict[str, Any]) -> None:
        """
        Send a single CAN message.
        """
        if not self.bus:
            self.log.error(f"Bus not connected, cannot send message")
            return

        try:
            msg = can.Message(
                arbitration_id=msg_data["id"],
                data=msg_data["data"],
                is_extended_id=False,
            )
            
            # can config allow sending
            if self.cc.send:                
                self.bus.send(msg)
                self.sent_count += 1
                self.log.debug(f"Sent message #{self.sent_count}")
                
        except Exception as e:
            self.log.error(f"Failed to send message: {e}")

    def loop(self, q_in: Queue, q_out: Queue) -> None:
        """
        Main loop: send messages from q_out and receive messages into q_in.
        """
        if not self.bus:
            self.connect()

        while not self.stop_event.is_set():
            # Send all queued messages
            while not q_out.empty():
                msg_data = q_out.get()
                self.send_message(msg_data)

                #self.log.debug(f"Message sent from queue: {msg_data}")

            # Receive CAN message with timeout
            msg = self.bus.recv(timeout=0.01)  # 100 Hz polling
            if msg:
                q_in.put(msg)

                #self.log.debug(f"Received message: {msg}")

