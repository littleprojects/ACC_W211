import time
import can
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
        interface: str,
        channel: str,
        bitrate: int,
        log,
        app_name: str,
        stop_event: Event,
        retry_in_sec: int = 5,
        filter_list: Optional[list] = None,
    ):
        self.log = log
        self.bus: Optional[can.BusABC] = None

        # Connection parameters
        self.interface = interface
        self.channel = channel
        self.app_name = app_name
        self.stop_event = stop_event
        self.bitrate = int(bitrate)
        self.retry_in_seconds = int(retry_in_sec)

        # Filters
        self.filter_list = filter_list

        # Counter for sent messages
        self.sent_count = 0

    def connect(self) -> Optional[can.BusABC]:
        """
        Try to connect to the CAN bus. Retries until successful.
        """
        self.log.info(f"CAN_{self.channel}: Connecting to CAN")
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
            self.log.error(f"CAN_{self.channel}: Connection failed: {e} --- retry")
            self.shutdown_connection()
            self.log.debug(f"CAN_{self.channel}: Retrying in {self.retry_in_seconds} seconds")
            time.sleep(self.retry_in_seconds)
            return self.connect()

    def set_filter(self, filter_list: Optional[list]) -> None:
        """
        Apply CAN filters to reduce load.
        """
        if not self.bus or not filter_list:
            return
        try:
            self.log.debug(f"CAN_{self.channel}: Setting filters {filter_list}")
            self.bus.set_filters(filter_list)
        except Exception as e:
            self.log.warning(f"CAN_{self.channel}: Cannot set filters: {e}")

    def shutdown_connection(self) -> None:
        """
        Shut down the CAN bus connection.
        """
        self.log.debug(f"CAN_{self.channel}: Shutting down connection")
        if self.bus:
            try:
                self.bus.shutdown()
            except Exception as e:
                self.log.error(f"CAN_{self.channel}: Shutdown failed: {e}")

    def send_message(self, msg_data: Dict[str, Any]) -> None:
        """
        Send a single CAN message.
        """
        if not self.bus:
            self.log.error(f"CAN_{self.channel}: Bus not connected, cannot send message")
            return

        try:
            msg = can.Message(
                arbitration_id=msg_data["id"],
                data=msg_data["data"],
                is_extended_id=False,
            )
            self.bus.send(msg)
            self.sent_count += 1
            self.log.debug(f"CAN_{self.channel}: Sent message #{self.sent_count}")
        except Exception as e:
            self.log.error(f"CAN_{self.channel}: Failed to send message: {e}")

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

            # Receive CAN message with timeout
            msg = self.bus.recv(timeout=0.01)  # 100 Hz polling
            if msg:
                q_in.put(msg)
