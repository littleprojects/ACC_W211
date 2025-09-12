
"""
this class reads and combine the configs

"""

import os
import logging
import configparser

from lib import utils

class Dict2Obj(object):
    """
    Transform a dict into an object
    """
    def __init__(self, d):
        for k, v in d.items():
            if isinstance(k, (list, tuple)):
                setattr(self, k, [obj(x) if isinstance(x, dict) else x for x in v])
            else:
                setattr(self, k, obj(v) if isinstance(v, dict) else v)


class Config:
    """
    Read the config file and merge it with the default_config
    Data from the config file will overwrite the default_config
    """

    def __init__(self, name, default_config, log):

        self.name = name
        self.default_config = default_config
        self.config = {}
        self.config_obj = None

        self.log = log

        # --------- CONFIG FILE ---------------
        # remember config argument types
        default_config_backup = {}

        # copy dict
        for key in self.default_config:
            default_config_backup[key] = self.default_config[key]

        self.log.debug('default_config: ' + str(default_config))

        # check, read and merge config from CONFIG FILE
        if self.default_config['config_file'] is not None:
            if os.path.exists(self.default_config['config_file']):
                
                self.log.info('Load config ['+self.name+'] from: ' + self.default_config['config_file'])

                # read configs
                conf_from_file = self.read_config(self.default_config['config_file'], self.name)
                self.log.debug('Config read from file: ' + str(conf_from_file))

                # merge configs from file with defaults
                #self.basic_config   = {**self.basic_config, **basic_conf_from_file} #merge default dictionary with config dict from file
                self.config = {**self.default_config,  **conf_from_file} #merge config with config from file
                self.log.debug('Merge Config: ' + str(self.config))
            else:
                self.log.warning('Config file not found. Please check: ' + self.default_config['config_file'])

        # parse arguments from config file to origanal type
        for key in default_config_backup:
            # get datatype from default setting
            data_type = type(default_config_backup[key])

            # get new value from merge
            value = self.config[key]

            # check data types and parse value to this type
            if data_type is bool:
                self.config[key] = utils.str_to_bool(value)
                #self.log.debug('parse ' + key + ' to bool: ' + str(value))
            if data_type is int:
                self.config[key] = utils.parse_number(value, 0)
                #self.log.debug('parse ' + key + ' to int: ' + str(value))
            if data_type is float:
                self.config[key] = float(value)

        # create the config object
        self.config_obj = Dict2Obj(self.config)

        # update logger with new setting
        #self.log.set_config(self.config)

    #def get_config(self):
    #    return self.config

    def read_config(self, file, section, as_obj=False):
        """
        Read the section form the config file
        :param file: path and name of the config file
        :param section: name of the section in the file
        :return: dict object with params and values from the config file or None
        """
        # print(file)
        # print(group)

        config = configparser.ConfigParser()
        config.read(file)

        # self.log.info(str(config.has_section(section)))

        if config.has_section(section):
            self.log.debug('config section found ' + section)
            return dict(config[section])
        else:
            # no section found - return empty dict
            self.log.warning(
                'Config section NOT found: config file: ' + file + '; Module: ' + self.name + '; config group MISSING: [' + section + ']; use default settings')
            return dict()
    

