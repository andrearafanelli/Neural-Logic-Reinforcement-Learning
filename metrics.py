import os
from datetime import datetime
import logging


class Metrics:
    def __init__(self, path: str, metric_fname: str, columns: list):
        self._path = path
        self._columns = columns
        file_name = os.path.join(self._path, f'{metric_fname}_{datetime.now().strftime("%Y%m%d-%H%M")}.log')
        os.makedirs(self._path, exist_ok=True)
        self._file = open(file_name, mode='w', newline='')
        row = ' '.join(self._columns)
        self._file.write(f"{row}\n")

    def log(self, values: list):
        if len(values) == len(self._columns):
            row = '\t'.join([str(i) for i in values])
            self._file.write(f'{row}\n')

    def close(self):
        self._file.close()


class MetricsLogger(Metrics):

    def __init__(self, path: str, metric_fname: str, columns: list):
        super().__init__(path, metric_fname, ['date', 'time', 'log-type'] + columns)
        self._file.close()
        self._file = None
        logging.basicConfig(filename=f'{self._path}/{metric_fname}_{datetime.now().strftime("%Y%m%d-%H%M")}.log',
                            format='%(asctime)s %(levelname)s %(message)s',
                            level=logging.DEBUG,
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filemode="a")

    def log(self, step:int, values:list):
        if len(values) == len(self._columns) - 3:
            msg = ""
            for v in values:
                msg += f"{v} "
            print("log:", step, msg)
            logging.info(f"{step} {msg}")
        else:
            logging.debug(f"values not matching columns: {values}")

    def debug(self, step: int, msg):
        logging.debug(f"{step} {msg}")

    def close(self):
        pass
