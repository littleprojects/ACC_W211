"""
MDF logging helper for recording CAN signals into MDF files.

"""

import time
import cantools

from enum import Enum
from typing import Any, Dict, Optional

from asammdf import MDF, Signal

from lib import utils
from lib.Logger import Log


class Mdf:
    """
    Creates MDF files to log CAN data.
    """

    def __init__(self, config_mdf):

        self.config = config_mdf
        
        self.log = Log('MDF', config=self.config).get_logger()
        
        self.file_name = self.config.log_file
        self.save_interval = int(self.config.interval_save)
        self.recording = self.config.enable

        # Start time for relative timestamps with ms
        self.ts_start = time.time()

        # Signal storage
        self.data: Dict[str, Dict[str, Any]] = {}
        self.counter = 0

        # CAN database - lookup from unit and comment
        self.dbc = None 
        # load DBC
        try:
            if self.config.dbc is not '':
                self.dbc = cantools.database.load_file(self.config.dbc)
        except Exception as e:
            self.log.warning('Cant load DBC: ' + self.config.dbc + str(e))

        if self.recording:
            self.log.info(f"MDF logging to file: {self.file_name}")
        else:
            self.log.info("MDF logging is deactivated")

    def new_signal(self, name: str, unit: str = "", comment: str = "") -> None:
        """
        Create or update a signal entry.
        """
        # TODO add a signal source to group signals by it

        if name not in self.data:
            self.data[name] = {"data": [], "ts": [], "unit": unit, "comment": comment}
        else:
            # Update metadata only
            self.data[name]["unit"] = unit
            self.data[name]["comment"] = comment

        self.log.debug(f"Signal added/updated: {name} ({unit}, {comment})")

    def add_signal(self, name: str, data: Any, ts_now: Optional[float] = None, signal_prefix: str = "", unit: str = "", comment: str = "") -> None:
        """
        Add a single signal value with timestamp.

        ts_now optional timestamp
        """

        if not self.recording:
            # recording is disabled
            return

        ts = time.time() - self.ts_start
        
        # optional TS is set
        if ts_now is not None:
            ts = ts_now 

        if name not in self.data:
            # Lookup unit/comment from DBC if available
            if self.dbc is not None:
                sig = utils.dbc_signal(self.dbc, name)
                if sig:
                    unit = sig.unit or unit
                    comment = sig.comments.get(None) or comment
                
            self.new_signal(signal_prefix+name, unit, comment)

        # save data
        self.data[signal_prefix+name]["data"].append(data)
        self.data[signal_prefix+name]["ts"].append(ts)

    def add_signals(self, signals: Dict[str, Any], signal_prefix: str = "") -> None:
        """
        Add multiple signals at once.
        """
        ts_now = time.time() - self.ts_start

        # input check
        if signals is None:
            return False
        
        #try:
        for key, value in signals.items():
            #name = f"{signal_prefix}{key}"
            
            # skip empty data
            #if key is None:
            #    continue
            #if value is None:
            #    continue

            # enum detection
            if isinstance(value, Enum):
                continue

            # if value have a dictionary-> recursiv call
            if isinstance(value, dict):
                self.add_signals(value, signal_prefix+key+'_')
                continue

            self.add_signal(key, value, ts_now, signal_prefix)

        # Autosave after N messages
        if self.save_interval > 0 and self.counter % self.save_interval == 0:
            self.write_mdf()

        self.counter += 1
        #except Exception as e:
            #self.log.error(f"Cannot add signals: {e}, {signals}")

    def write_mdf(self) -> bool:
        """
        Write all signals to MDF file.
        """
        if not self.recording:
            # recording is disabled
            self.data.clear()
            return False

        mdf = MDF(version="4.10")

        self.log.info(f"Writing file: {self.file_name}")

        for name, sig_data in self.data.items():
            length = min(len(sig_data["data"]), len(sig_data["ts"]))
            
            # skip empty records
            if length == 0:
                continue

            sig = Signal(
                sig_data["data"][:length],
                timestamps=sig_data["ts"][:length],
                name=name,
                unit=sig_data.get("unit", ""),
                comment=sig_data.get("comment", ""),
            )

            self.log.debug(f"Appending signal: {name}, unit={sig.unit}, comment={sig.comment}")
            mdf.append([sig])

        try:
            mdf.save(self.file_name, overwrite=True, compression=True)
            mdf.close()
            return True
        except Exception as e:
            self.log.warning(f"Cannot write MDF file: {e}")
            mdf.close()
            return False
