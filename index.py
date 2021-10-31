import logging
import os
import sys
import threading
import time

import dotenv
from PyQt5 import QtWidgets, QtGui
from PyQt5.uic import loadUi

from requester import Requester, Response
import resources


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('main.ui', self)

        self._logger = logging.getLogger('index')
        self.pageList = ['homePage', 'logsPage']

        self.initUi()

        self._requester = Requester(os.environ.get('APPLICATION_URL'))
        self._loggingHandler = threading.Thread(
            target=self.requestHandling,
            daemon=True
        )

        self._requester.start()
        self._loggingHandler.start()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self._logger.info('Closing MainWindow')
        self._requester.close()
        self._logger.info('MainWindow has been successfully closed')

    def initUi(self):
        self._logger.info('Initializing MainWindow\s UI')

        # Navigation
        for i in ['home_2', 'logs_2']:
            eval(f'self.{i}').clicked.connect(self.onNavChecked)

        # Controls
        for i in ['launch', 'terminate', 'restart']:
            eval(f'self.{i}').clicked.connect(self.onControlBtnClick)

        self._logger.info('Initialized UI, going further')

    def requestHandling(self):
        while True:
            response = self._requester.response
            if response:
                try:
                    validated = Response(**response.json())
                except Exception as e:
                    self._logger.warning(e)

            time.sleep(5)

    def onControlBtnClick(self):
        print(self.sender().objectName())

    def onNavChecked(self):
        name = self.sender().objectName()
        page = name[:name.index('_')] + 'Page'
        self.pages.setCurrentIndex(self.pageList.index(page))


def hook(*args):
    sys.__excepthook__(*args)


if __name__ == '__main__':
    dotenv.load_dotenv('./.env')

    logging.basicConfig(level=logging.WARNING,
                        format='%(asctime)s - %(levelname)s - %(name)s:\t%(message)s',
                        datefmt='%y.%b.%Y %H:%M:%S')

    app = QtWidgets.QApplication([])
    window = MainWindow()
    sys.__excepthook__ = hook

    window.show()
    app.exec()
