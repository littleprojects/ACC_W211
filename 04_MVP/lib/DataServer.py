"""
Data Server for handling API requests.

Works with Flask to provide a RESTful API for accessing and manipulating data.
"""

import logging

from lib.Logger import Log
from flask import Flask, jsonify, request


class DataServer:
    def __init__(self, config_DS, art_data=None):
        
        self.config = config_DS
        self.art_data = art_data

        # Logger
        self.log = Log('DS', config=self.config).get_logger()

        self.app = Flask(__name__)
        self.host = self.config.host
        self.port = self.config.port

        # diable logging for Flask to avoid cluttering the console output
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        #log.disabled = True

        #self.app.logger.setLevel(logging.ERROR)
        #self.app.logger = log

        self.log.info(f"Data Server initialized on {self.host}:{self.port}")

        self.setup_routes()

    def run(self):
        self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)

    def cancel(self):
        self.app.shutdown()

    def setup_routes(self):
        @self.app.route("/")
        def index():
            return jsonify(message="Hallo World!"), 200

        @self.app.route("/data/<key>", methods=["GET"])
        def get_value(key):
            if key == 'can_c':
                return jsonify(self.art_data.get_vehicle_msgs()), 200
            elif key == 'radar':
                return jsonify(self.art_data.get_radar_msgs()), 200
            elif key == 'can_art':
                return jsonify(self.art_data.get_art_msg()), 200
            elif key == 'art_states':
                return jsonify(self.art_data.get_art_states()), 200
            else:
                return jsonify({"error": "Key not found"}), 404
            
    
    
