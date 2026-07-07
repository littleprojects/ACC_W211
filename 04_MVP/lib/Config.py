"""
This module reads and merges configuration files with default settings.
"""

import os
import configparser
from typing import Any, Dict

from lib import utils
from lib import Logger


class Dict2Obj:
    """
    Recursively transform a dict into an object with attribute access.
    """

    def __init__(self, d: Dict[str, Any]):
        for k, v in d.items():
            if isinstance(v, dict):
                setattr(self, k, Dict2Obj(v))
            elif isinstance(v, (list, tuple)):
                setattr(self, k, [Dict2Obj(x) if isinstance(x, dict) else x for x in v])
            else:
                setattr(self, k, v)


class Config:
    """
    Read the config file and merge it with the default_config.
    Data from the config file will overwrite the default_config.
    """

    def __init__(self, default_config: Dict[str, Any]):
        #self.name = name
        self.default_config = default_config.copy()
        self.config: Dict[str, Any] = default_config.copy()
        self.config_obj: Dict2Obj | None = None
        
        self.log = Logger.Log('CONFIG').get_logger()
        self.log.setLevel(Logger.parse_log_level(default_config.get('loglevel', 'INFO')))

        # self.log.debug(f"default_config: {self.default_config}")

        config_file = self.default_config.get("config_file")

        if config_file and os.path.exists(config_file):
            self.log.info(f"Load Config from: {config_file}")

            conf_from_file = self.read_config(config_file)
            
            self.log.debug(f"Config read from file: {conf_from_file}")

            # Merge defaults with file config
            #self.config.update(conf_from_file)

            # merge dictionaries
            self.config = self.recursive_merge(self.default_config, conf_from_file)

            self.log.debug(f"Merged Config: {self.config}")
        elif config_file:
            self.log.warning(f"Config file not found. Please check: {config_file}")

        # Parse values back to original types
        self._parse_types(default_config)

        # print config
        # self.print_config()
        self.log.debug(f"Config: {self.config}")

        # Create object representation
        self.config_obj = Dict2Obj(self.config)

    def _parse_types(self, default_config: Dict[str, Any]) -> None:
        """Ensure values from config file are cast to the types of defaults."""
        for key, default_value in default_config.items():
            if key not in self.config:
                continue
            value = self.config[key]
            if isinstance(default_value, bool):
                self.config[key] = utils.str_to_bool(value)
            elif isinstance(default_value, int):
                self.config[key] = utils.parse_number(value, 0)
            elif isinstance(default_value, float):
                self.config[key] = float(value)

    def recursive_merge(self, dict1, dict2):
        for key, value in dict2.items():
            if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                dict1[key] = self.recursive_merge(dict1[key], value)
            else:
                # Merge non-dictionary values
                dict1[key] = value
        return dict1

    def read_config(self, file: str):
        """
        Read the section from the config file.
        Returns a dict with params and values from the config file.
        """
        config_dict = {}

        config = configparser.ConfigParser()
        config.read(file)

        for section in config.sections():
            #print(f"[{section}]")
            config_dict[section] = {}

            #config_dict[section] = config[section]

            for key, val in config.items(section):
                #print(f"{key} = {val}")
                config_dict[section].update({key: val})

        return config_dict

        #if config.has_section(section):
        #    self.log.debug(f"Config section found: {section}")
        #    return dict(config[section])
        #else:
        #    self.log.warning(
        #        f"Config section NOT found: file={file}; module={self.name}; "
        #        f"missing group=[{section}]; using default settings!"
        #    )
        #    return {}

    def print_config(self):
        """Return a formatted string of the current config."""
        self.log.debug('Config:\n' + "\n".join(f"{item}:\t{value}" for item, value in self.config.items()))
