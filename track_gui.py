import PySide2
from PySide2.QtWidgets import *
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from datetime import datetime
import sys
from back_end import *
import os
import re
import csv

import numpy as np
import random


# ------------------ MainWidget ------------------


class MainWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        designer_file = QFile("track.ui")
        designer_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.ui = loader.load(designer_file, self)
        designer_file.close()

        self.cwd = os.getcwd()
        date = datetime.today().strftime('%Y-%m-%d')
        self.save_path = self.cwd + '\\' + date
        self.ui.text_file_path_2.setText(self.save_path)
        self.parameter_dict = {
            'alpha': 3, 'beta': 0,
            'peak_circle': 6, 'peak_ratio': 0.4,
            'row_bias': 0, 'column_bias': 0,
            'label_radius': 7,
            'right_black': 0, 'left_black': 0,
            'right_black_bias': 0, 'left_black_bias': 0,
            'right_circle': 5, 'right_ratio': 0.6,
            'left_circle': 5, 'left_ratio': 0.6,
        }


        self.thread = QThread()
        # 实例化线程类
        self.i_thread = ImageProcessingThread()
        # moveToThread方法把实例化线程移到Thread管理
        self.i_thread.moveToThread(self.thread)
        # 连接槽函数
        self.i_thread.start_image_process_thread_signal.connect(self.i_thread.loop)
        self.i_thread.show_img_signal.connect(self.show_image)

        # 开启线程,一直挂在后台
        # 开启线程,一直挂在后台
        self.thread.start()

    def button_saving_folder(self):
        self.save_path, _ = QFileDialog.getSaveFileName(self, 'Select save path', self.cwd, 'Image(*.tif)')
        self.ui.text_file_path_2.setText(self.save_path)

    def open(self):
        self.i_thread.is_killed = False
        self.i_thread.track = False
        self.i_thread.record = False

    def track(self):
        self.i_thread.track = True

    def record(self):
        self.i_thread.record = True

    def button_kill(self):
        self.i_thread.is_killed = True

    def button_pause(self):
        if not self.i_thread.is_paused:
            self.i_thread.is_paused = True
            self.ui.button_pause.setText("Resume")
        else:
            self.i_thread.is_paused = False
            self.ui.button_pause.setText("Pause")

    def show_image(self, q_pixmap):
        self.ui.label_image.setPixmap(q_pixmap)

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self,
                                               'Quit',
                                               "Quit?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
            os._exit(0)
        else:
            event.ignore()



if __name__ == '__main__':
    dirname = os.path.dirname(PySide2.__file__)
    plugin_path = os.path.join(dirname, 'plugins', 'platforms')
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
    print(plugin_path)
    app = QApplication([])
    window = MainWidget()
    window.show()
    app.exec_()
