import time
from typing import Any, Dict, Optional

from asammdf import MDF, Signal
from lib import utils


class Mdf:
    """
    Creates MDF files to log CAN data.
    """

    def __init__(
        self,
        file_name: str,
        log,
        dbc: Optional[Any] = None,
        save_interval: int = 0,
        recording: bool = True,
    ):
        self.log = log
        self.file_name = file_name
        self.dbc = dbc
        self.save_interval = save_interval
        self.recording = recording

        # Start time for relative timestamps
        self.ts_start = time.time()

        # Signal storage
        self.data: Dict[str, Dict[str, Any]] = {}
        self.counter = 0

        if recording:
            self.log.info(f"MDF logging to file: {file_name}")
        else:
            self.log.info("MDF logging is deactivated")

    def new_signal(self, name: str, unit: str = "", comment: str = "") -> None:
        """
        Create or update a signal entry.
        """
        if name not in self.data:
            self.data[name] = {"data": [], "ts": [], "unit": unit, "comment": comment}
        else:
            # Update metadata only
            self.data[name]["unit"] = unit
            self.data[name]["comment"] = comment

        self.log.debug(f"Signal added/updated: {name} ({unit}, {comment})")

    def add_signal(
        self,
        name: str,
        data: Any,
        ts_now: Optional[float] = None,
        unit: str = "",
        comment: str = "",
    ) -> None:
        """
        Add a single signal value with timestamp.
        """
        ts = ts_now if ts_now is not None else time.time() - self.ts_start

        if name not in self.data:
            # Lookup unit/comment from DBC if available
            if self.dbc is not None:
                sig = utils.dbc_signal(self.dbc, name)
                if sig:
                    unit = sig.unit or unit
                    comment = sig.comments.get(None) or comment
            self.new_signal(name, unit, comment)

        if self.recording:
            self.data[name]["data"].append(data)
            self.data[name]["ts"].append(ts)

    def add_signals(self, signals: Dict[str, Any], signal_prefix: str = "") -> None:
        """
        Add multiple signals at once.
        """
        ts_now = time.time() - self.ts_start
        try:
            for key, value in signals.items():
                name = f"{signal_prefix}{key}"
                self.add_signal(name, value, ts_now)

            # Autosave after N messages
            if self.save_interval > 0 and self.counter % self.save_interval == 0:
                self.write_mdf()

            self.counter += 1
        except Exception as e:
            self.log.error(f"MDF: Cannot add signals: {e}")

    def write_mdf(self) -> bool:
        """
        Write all signals to MDF file.
        """
        if not self.recording:
            self.data.clear()
            return False

        mdf = MDF(version="4.10")
        self.log.info(f"MDF: Writing file: {self.file_name}")

        for name, sig_data in self.data.items():
            length = min(len(sig_data["data"]), len(sig_data["ts"]))
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
            return True
        except Exception as e:
            self.log.error(f"MDF: Cannot write MDF file: {e}")
            return False
