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
        self._res = None
        self._logger = logging.getLogger('requester')

    @property
    def response(self) -> Union[dict, None]:
        self._logger.info(f'Requesting {self._url}...')
        try:
            # Status
            self._logger.info(f'Getting bot status')
            _status = requests.get(self._url)
            _status = _status.json()['status'] if _status.ok else 'unknown'

            # Vars
            self._logger.info(f'Getting variables via {self._url + "vars"}')
            _vars = requests.get(self._url + 'vars')
            _vars = Vars(**_vars.json()) if _vars.ok else Vars(
                latency=float('Nan'),
                servers=[],
                memory_used=float('Nan')
            )

            # Log
            self._logger.info(f'Getting logs via {self._url + "log"}')
            _log = requests.get(self._url + 'log')
            _log = Log(**_log.json()) if _log.ok else Log(content='')
        except requests.exceptions.RequestException:
            _status = 'unknown'
            _log = Log(content='')
            _vars = Vars(
                latency=float('Nan'),
                servers=[],
                memory_used=float('Nan')
            )

            self._logger.warning(f'Failed requesting {self._url}...')

        return {
            'status': _status,
            'log': _log,
            'vars': _vars
        }


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
