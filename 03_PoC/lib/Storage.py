"""
This Class is about to read and write to a local persistent file
to store information and load it at the next run.
"""

import os
import json
from pathlib import Path

class Storage:

    def __init__(self, path_to_file, data, log=None):

        # data dict example
        # data = { 'file_cnt':0 }
        self.data = data

        self.path_to_file = path_to_file

        self.path_to_file = Path(self.path_to_file).resolve()

        self.log = log

        os.makedirs(os.path.dirname(self.path_to_file), exist_ok=True)

        if os.path.isfile(self.path_to_file):
            self.read()
        else:
            self.write()

    def read(self):

        if self.log is None:
            print('Read data from: ' + str(self.path_to_file))
        else:
            self.log.info('Read data from: ' + str(self.path_to_file))

        # read data from file
        with open(self.path_to_file, 'r') as file:
            # parse from JSON
            self.data = json.load(file)

        return self.data

    def write(self, data=None):

        write_data = data

        if data is None:
            write_data = self.data

        if self.log is None:
            print('Write data to: ' + str(self.path_to_file))
        else:
            self.log.info('Write data to: ' + str(self.path_to_file))

        with open(self.path_to_file, 'w') as file:
            json.dump(write_data, file)


if __name__ == "__main__":

    file = 'storage.txt'
    data = { 'i': 0}

    store = Storage(file, data)

    print(store.data)

    data = store.read()
    print(data)

    data['i'] += 1

    store.write(data)

    data = store.read()
    print(data)