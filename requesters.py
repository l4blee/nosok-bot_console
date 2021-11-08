import logging
import os
from typing import Union
from dotenv import load_dotenv

import pydantic
import requests

load_dotenv('.env')


class GetRequester:
    def __init__(self, url):
        self._url = url
        print(url)
        self._res = None
        self._logger = logging.getLogger('requester')

    @property
    def response(self) -> Union[dict, None]:
        self._logger.info(f'Requesting {self._url}...')
        try:
            # Vars
            self._logger.info(f'Getting variables via {self._url + "vars"}')
            _vars = requests.get(self._url + 'vars')
            if _vars is not None:
                _vars = Vars(**_vars.json())

            # Log
            self._logger.info(f'Getting logs via {self._url + "log"}')
            _log = requests.get(self._url + 'log')
            if _log is not None:
                _log = Log(**_log.json())

            return {
                'log': _log,
                'vars': _vars
            }
        except requests.exceptions.RequestException:
            self._logger.warning(f'Failed requesting {self._url}...')


class PostRequester:
    def __init__(self, url):
        self._url = url
        self._res = None
        self._logger = logging.getLogger('requester')

        self.user = os.environ.get('app_username')
        self.password = os.environ.get('app_password')

    def post(self, instruction):
        payload = {
            'Authorization': f'{self.user}:{self.password}'
        }

        res = requests.post(self._url + instruction, headers=payload)
        return res


class Vars(pydantic.BaseModel):
    latency: float
    servers: list[int]
    memory_used: float


class Log(pydantic.BaseModel):
    content: str


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING,
                        format='%(asctime)s - %(levelname)s - %(name)s:\t%(message)s',
                        datefmt='%y.%b.%Y %H:%M:%S')
    url = 'http://localhost:5000/'

    getter = GetRequester(url)
    poster = PostRequester(url)

    # print(getter.response)
    print(poster.post)
