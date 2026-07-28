"""
This Class is about to read and write to a local persistent file
to store information and load it at the next run.
"""

import os
import json

from pathlib import Path

class Storage:

    def __init__(self, path_to_file, default_data, log=None):

        self.log = log

        # data dict example
        # data = { 'file_cnt':0 }
        self.data = default_data # default data

        # store as a pathlib.Path, expand user and resolve to absolute
        self.path_to_file = Path(str(path_to_file)).expanduser().resolve()

        # ensure parent directory exists
        self.path_to_file.parent.mkdir(parents=True, exist_ok=True)

        # use pathlib checks
        if self.path_to_file.is_file():
            self.read()
        else:
            if self.log is not None:
                self.log.warning('Persistent Storage file NOT found. Write defaults.')
            self.write() # create file if not exist

    def read(self):

        if self.log is None:
            print('Read data from: ' + str(self.path_to_file))
        else:
            self.log.debug('Read data from: ' + str(self.path_to_file))

        try:
            # read data from file
            with self.path_to_file.open('r', encoding='utf-8') as file:
                # parse from JSON
                loaded_data = json.load(file)
                # merge loaded data into dataset -> new data will added smooth
                self.data.update(loaded_data)
        except Exception:
            if self.log is not None:
                self.log.warning('Cant read persitant storage. Check: ' + str(self.path_to_file))

        return self.data

    def write(self, data=None):

        write_data = data

        if data is None:
            write_data = self.data

        if self.log is None:
            print('Write data to: ' + str(self.path_to_file))

        else:
            self.log.debug('Write data to: ' + str(self.path_to_file))

        with self.path_to_file.open('w', encoding='utf-8') as file:
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