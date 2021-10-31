import requests
import pydantic
import logging
import threading
import time
from typing import Union


class Requester(threading.Thread):
    def __init__(self, url):
        super(Requester, self).__init__(
            target=self.loop,
            daemon=True
        )

        self._url = url
        self._res = None
        self._logger = logging.getLogger('requester')
        self._stop = threading.Event()

    @property
    def response(self) -> Union[requests.Response, None]:
        return self._res

    @property
    def stopped(self):
        return self._stop.is_set()

    def loop(self) -> None:
        while True:
            self._logger.info(f'Requesting {self._url}...')
            try:
                self._res = requests.get(self._url)
            except requests.exceptions.RequestException:
                self._logger.warning(f'Failed requesting {self._url}...')
            else:
                self._logger.info('Got response, now sleeping')
            time.sleep(5)

    def start(self) -> None:
        self._logger.info('Launching Requester')
        super(Requester, self).start()
        self._logger.info('Requester has been successfully launched')

    def close(self):
        self._logger.info('Closing Requester')
        self._logger.info('Stopping Requester\'s thread')
        self._stop.set()
        self._logger.info('Requester has been successfully stopped')


class Response(pydantic.BaseModel):
    latency: float
    servers: list[int]
    memory_used: float
