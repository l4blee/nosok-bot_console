import io
import json
import logging
import os
import sys
import time

import dotenv
import matplotlib.pyplot as plt
from PIL import Image
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QPixmap, QFontDatabase, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi

from requesters import GetRequester, PostRequester, Vars
import resources

CHART_WIDTH = 320


class GetHandler(QObject):
    done = pyqtSignal(object)
    getter = GetRequester(os.environ.get('APPLICATION_URL'))

    def loop(self):
        while True:
            response = self.getter.response
            self.done.emit(response)

            time.sleep(5)


class PostHandler(QObject):
    done = pyqtSignal(object)
    poster = PostRequester(os.environ.get('APPLICATION_URL'))

    def post(self, instruction):
        res = self.poster.post(instruction)
        if not res.ok:
            pass
        self.done.emit(res.status_code)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('main.ui', self)

        self._logger = logging.getLogger('index')
        self.pageList = ['homePage', 'logsPage']

        self.initUi()

        self._thread = QThread()

        self.get_handler = GetHandler()
        self.get_handler.done.connect(self.onRequestReady)

        self.post_handler = PostHandler()

        self.post_handler.moveToThread(self._thread)
        self.get_handler.moveToThread(self._thread)

        self._thread.started.connect(self.get_handler.loop)

        self.latency_log = [-2 for _ in range(10)]
        self.memory_usage_log = [-2 for _ in range(10)]

        self._thread.start()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self._logger.info('Closing MainWindow')
        super().closeEvent(event)
        self._logger.info('MainWindow has been successfully closed')

    def initUi(self):
        self._logger.info('Initializing MainWindow\'s UI')

        # Navigation
        for i in ['home', 'logs']:
            eval(f'self.{i}').clicked.connect(self.onNavChecked)

        # Bot controls
        for i in ['launch', 'terminate', 'restart']:
            eval(f'self.{i}').clicked.connect(self.onControlBtnClick)

        # Window controls
        self.close_btn.clicked.connect(self.close)
        self.minimize_btn.clicked.connect(self.showMinimized)
        self.maximize_btn.clicked.connect(self.maximizeEvent)

        self.topBar.mouseMoveEvent = self.moveWindow

        # Other settings
        self.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        self._logger.info('Initialized UI, starting application...')

    def maximizeEvent(self):
        if self.isMaximized():
            self.centralWidget().setStyleSheet(
                '#centralwidget {\n'
                'background-color: rgb(244, 152, 128);\n'
                'border: 1px transparent;\n'
                'border-radius: 20px;\n'
                '}')
            self.maximize_btn.setToolTip('Maximize')
            self.showNormal()
        else:
            self.centralWidget().setStyleSheet(
                '#centralwidget {\n'
                'background-color: rgb(244, 152, 128);\n'
                'border: none;\n'
                '}')
            self.maximize_btn.setToolTip('Restore')
            self.showMaximized()

    def moveWindow(self, event):
        if event.buttons() == Qt.LeftButton:
            if self.isMaximized():
                self.maximizeEvent()

            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
            event.accept()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        self.dragPos = event.globalPos()

    def onRequestReady(self, signal: dict):
        if signal is None:
            return

        self.updateLogs(signal)
        self.updateStatus(signal)
        self.updateVars(signal)

    def updateVars(self, signal: dict):
        vars_: Vars = signal['vars']
        data = json.loads(vars_.json())
        latency, servers, memory = data.values()

        self.servers.setText(f'Servers: {len(servers)}')
        self.title_mem.setText(f'Memory: {memory:.2f} MB')
        self.title_lat.setText(f'Latency: {latency:.2f} s')

        del self.memory_usage_log[0]
        self.memory_usage_log.append(round(memory, 2))

        del self.latency_log[0]
        self.latency_log.append(round(latency, 2))

        # Memory usage chart
        fig: plt.Figure = plt.figure(figsize=(4, 4))
        y = self.memory_usage_log
        x = list(range(10))
        plt.bar(x, y, width=0.9, color='#bfbf01')
        plt.xticks(x)
        plt.ylim([0, 512])
        plt.margins(0.015, tight=True)
        plt.tight_layout()
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png')
        plt.close(fig)

        img = Image.open(buffer, formats=['png'])
        img = img.resize((CHART_WIDTH, CHART_WIDTH))
        pixmap = self.convertImage(img)
        self.memory.setPixmap(pixmap)

        # Latency changes chart
        fig: plt.Figure = plt.figure(figsize=(4, 4))
        y = self.latency_log
        x = list(range(10))
        plt.bar(x, y, width=0.9, color='#bfbf01')
        plt.xticks(x)
        plt.ylim([0, 0.5])
        plt.margins(0.015, tight=True)
        plt.tight_layout()
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png')
        plt.close(fig)

        img = Image.open(buffer, formats=['png'])
        img = img.resize((CHART_WIDTH, CHART_WIDTH))
        pixmap = self.convertImage(img)
        self.latency.setPixmap(pixmap)

    @staticmethod
    def convertImage(im):
        im2 = im.convert('RGBA')
        data = im2.tobytes('raw', 'RGBA')
        qim = QImage(data, im.size[0], im.size[1], QImage.Format_ARGB32)
        pixmap = QPixmap.fromImage(qim)
        return pixmap

    def updateLogs(self, signal: dict):
        self.logger.setPlainText(signal['log'].content)
        self.logger.moveCursor(QtGui.QTextCursor.End)

    def updateStatus(self, signal: dict):
        self.status.setText(
            f'Bot status:\n{signal["status"]}'
        )

    def onControlBtnClick(self):
        instruction = self.sender().objectName()
        self.post_handler.post(instruction)

    def onNavChecked(self):
        page = self.sender().objectName() + 'Page'
        self.pages.setCurrentIndex(self.pageList.index(page))


def hook(*args):
    sys.__excepthook__(*args)


if __name__ == '__main__':
    dotenv.load_dotenv('./.env')
    pyqt_plugins = 'venv/Lib/site-packages/PyQt5/Qt5/plugins/platforms'
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = pyqt_plugins

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(name)s:\t%(message)s',
                        datefmt='%y.%b.%Y %H:%M:%S')

    app = QApplication([])
    QFontDatabase.addApplicationFont('sources/fonts/Montserrat-Regular.ttf')
    window = MainWindow()
    sys.__excepthook__ = hook

    window.show()
    app.exec()

    del window, app
