import PySide2
from PySide2.QtWidgets import *
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import sys
from analysis_back import *
import os
import re
import csv

import numpy as np
import random



# ------------------ MplWidget ------------------
class MplWidget(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.canvas = FigureCanvas(Figure())

        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(self.canvas)
        vertical_layout.addWidget(NavigationToolbar(self.canvas, self))

        self.canvas.axes = self.canvas.figure.add_subplot(111)
        self.setLayout(vertical_layout)

    # ------------------ MainWidget ------------------


class MainWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        designer_file = QFile("ui.ui")
        designer_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        loader.registerCustomWidget(MplWidget)
        self.ui = loader.load(designer_file, self)

        designer_file.close()

        self.image_name = ''
        self.image_path = ''
        self.cwd = os.getcwd()
        self.save_path = self.cwd + '\\1.csv'

        self.ui.text_file_path_2.setText(self.save_path)

        self.image_num = 0
        self.image_8bit = None
        self.image_16bit = None
        self.image_bright = None

        self.stop = False
        self.flip = False

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

        self.initialization_parameter()

        self.result_dict = {}
        self.results = []

        self.image_nums = []
        self.right_brightness = []
        self.left_brightness = []
        self.brightness = []

        self.rows =[]
        self.columns =[]

        self.thread = QThread()
        # 实例化线程类
        self.i_thread = ImageProcessingThread()
        # moveToThread方法把实例化线程移到Thread管理
        self.i_thread.moveToThread(self.thread)
        # 连接槽函数
        self.i_thread.start_image_process_thread_signal.connect(self.i_thread.image_processing)
        self.i_thread.show_img_signal.connect(self.show_image)
        self.i_thread.show_img_signal_loop.connect(self.show_image_loop)
        self.i_thread.loop_signal.connect(self.i_thread.loop)
        # 开启线程,一直挂在后台
        self.thread.start()

        # 部件处理
        self.ui.button_select_file.clicked.connect(self.button_select_file)
        self.ui.button_select_file_2.clicked.connect(self.button_save_data)

        self.ui.button_next.clicked.connect(self.button_next)
        self.ui.button_last.clicked.connect(self.button_last)

        self.ui.button_go.clicked.connect(self.button_go)
        self.ui.button_run.clicked.connect(self.button_run)
        self.ui.button_refresh.clicked.connect(self.button_refresh)

        self.ui.button_pause.clicked.connect(self.button_pause)
        self.ui.button_stop.clicked.connect(self.button_kill)

        self.ui.button_up.clicked.connect(lambda: self.button_refresh(-1, 0))
        self.ui.button_down.clicked.connect(lambda: self.button_refresh(1, 0))
        self.ui.button_left.clicked.connect(lambda: self.button_refresh(0, -1))
        self.ui.button_right.clicked.connect(lambda: self.button_refresh(0, 1))

        self.ui.checkbox_mirror_symmetry.stateChanged.connect(self.checkbox_mirror_symmetry)

        self.ui.text_file_path.setText(self.image_path)
        self.dataframe = pd.DataFrame(
            columns=['Right_row', 'Right_column', 'Right_brightness', 'Left_row', 'Left_column', 'Left_brightness',
                     'Brightness'])

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

    def button_save_data(self):
        self.save_path, _ = QFileDialog.getSaveFileName(self, 'Select save path', self.cwd, 'Table(*.csv)')
        self.ui.text_file_path_2.setText(self.save_path)

    def button_select_file(self):
        image_path_name, _ = QFileDialog.getOpenFileName(self, 'Select image', '', 'Image files(*.tif)')

        self.image_path, self.image_name = os.path.split(image_path_name)

        self.ui.text_file_path.setText(self.image_path)

        # if self.image_path == '':
        #     self.image_path = QFileDialog.getExistingDirectory(self, 'Select image')
        #     self.ui.text_file_path.setText(self.image_path)
        #     print(self.image_path)
        #     print('\nCancel')

        regex = re.compile(r'\d+')
        if bool(re.search(r'\d', self.image_name)):
            self.image_num = int(max(regex.findall(self.image_name)))
            print(self.image_num)

        self.set_parameter()
        self.i_thread.start_image_process_thread_signal.emit(self.parameter_dict,
                                                             self.image_num, self.image_path, self.flip)

    def button_next(self):
        self.image_num += 1
        self.set_parameter()
        self.i_thread.start_image_process_thread_signal.emit(self.parameter_dict,
                                                             self.image_num, self.image_path, self.flip)

    def button_last(self):
        self.image_num -= 1
        self.set_parameter()
        self.i_thread.start_image_process_thread_signal.emit(self.parameter_dict,
                                                             self.image_num, self.image_path, self.flip)

    def button_kill(self):
        self.i_thread.is_killed = True

    def button_pause(self):
        if not self.i_thread.is_paused:
            self.i_thread.is_paused = True
            self.ui.button_pause.setText("Resume")
        else:
            self.i_thread.is_paused = False
            self.ui.button_pause.setText("Pause")


    def button_go(self):
        self.image_num = int(self.ui.textEdit_num.toPlainText())
        self.set_parameter()
        self.i_thread.start_image_process_thread_signal.emit(self.parameter_dict,
                                                             self.image_num, self.image_path, self.flip)

    def button_run(self):
        self.results = []
        start = int(self.ui.textEdit_start.toPlainText())
        end = int(self.ui.textEdit_end.toPlainText())
        self.image_num = start
        self.set_parameter()
        self.i_thread.is_killed = False
        # for i in range(start, end + 1):
        # if self.stop:
        #     break
        self.i_thread.loop_signal.emit(self.parameter_dict,
                                       self.image_num, self.image_path,
                                       self.flip, start, end)
        self.image_num += 1

    def button_refresh(self, bias_row=0, bias_column=0):
        self.set_parameter()
        self.parameter_dict['row_bias'] += bias_row
        self.parameter_dict['column_bias'] += bias_column
        self.initialization_parameter()
        self.i_thread.start_image_process_thread_signal.emit(self.parameter_dict,
                                                             self.image_num, self.image_path, self.flip)

    def checkbox_mirror_symmetry(self):
        self.flip = not self.flip
        self.set_parameter()
        self.i_thread.start_image_process_thread_signal.emit(self.parameter_dict,
                                                             self.image_num, self.image_path, self.flip)

    def initialization_parameter(self):
        self.ui.textEdit_alpha.setText(str(self.parameter_dict['alpha']))
        self.ui.textEdit_beta.setText(str(self.parameter_dict['beta']))

        self.ui.textEdit_peak_ratio.setText(str(self.parameter_dict['peak_ratio']))
        self.ui.textEdit_peak_circle.setText(str(self.parameter_dict['peak_circle']))

        self.ui.textEdit_right_ratio.setText(str(self.parameter_dict['right_ratio']))
        self.ui.textEdit_right_circle.setText(str(self.parameter_dict['right_circle']))

        self.ui.textEdit_row_bias.setText(str(self.parameter_dict['row_bias']))
        self.ui.textEdit_column_bias.setText(str(self.parameter_dict['column_bias']))

        self.ui.textEdit_left_ratio.setText(str(self.parameter_dict['left_ratio']))
        self.ui.textEdit_left_circle.setText(str(self.parameter_dict['left_circle']))

        self.ui.textEdit_right_black_bias.setText(str(self.parameter_dict['right_black_bias']))
        self.ui.textEdit_left_black_bias.setText(str(self.parameter_dict['left_black_bias']))

    def set_parameter(self):
        self.parameter_dict['alpha'] = float(self.ui.textEdit_alpha.toPlainText())
        self.parameter_dict['beta'] = float(self.ui.textEdit_beta.toPlainText())

        self.parameter_dict['peak_ratio'] = float(self.ui.textEdit_peak_ratio.toPlainText())
        self.parameter_dict['peak_circle'] = int(self.ui.textEdit_peak_circle.toPlainText())

        self.parameter_dict['right_ratio'] = float(self.ui.textEdit_right_ratio.toPlainText())
        self.parameter_dict['right_circle'] = int(self.ui.textEdit_right_circle.toPlainText())

        self.parameter_dict['row_bias'] = int(self.ui.textEdit_row_bias.toPlainText())
        self.parameter_dict['column_bias'] = int(self.ui.textEdit_column_bias.toPlainText())

        self.parameter_dict['left_ratio'] = float(self.ui.textEdit_left_ratio.toPlainText())
        self.parameter_dict['left_circle'] = int(self.ui.textEdit_left_circle.toPlainText())

        self.parameter_dict['right_black_bias'] = int(self.ui.textEdit_right_black_bias.toPlainText())
        self.parameter_dict['left_black_bias'] = int(self.ui.textEdit_left_black_bias.toPlainText())

    def show_image(self, q_pixmap, result_dict):
        self.ui.label_image.setPixmap(q_pixmap)
        self.result_dict = result_dict
        self.set_result()
        self.results.append(result_dict)
        self.draw_brightness(result_dict)
        self.draw_position(result_dict)

    def show_image_loop(self, q_pixmap, result_dict):
        self.ui.label_image.setPixmap(q_pixmap)
        self.result_dict = result_dict
        self.set_result()
        self.results.append(result_dict)
        self.draw_brightness(result_dict)
        self.draw_position(result_dict)
        self.write_csv(result_dict, self.dataframe)


    def write_csv(self, result_dict, dataframe):

        dataframe = \
            dataframe.append(pd.DataFrame({
                'Right_row': [result_dict['right_row']],
                'Right_column': [result_dict['right_column']],
                'Right_brightness': [result_dict['right_brightness']],
                'Left_row': [result_dict['left_row']],
                'Left_column': [result_dict['left_column']],
                'Left_brightness': [result_dict['left_brightness']],
                'Brightness': [result_dict['brightness']]}),
                ignore_index=True)

        dataframe.to_csv(self.save_path, sep=',', encoding='utf-8')

    def draw_position(self, result_dict):
        self.rows.append(result_dict['right_row'])
        self.columns.append(result_dict['right_column'])
        self.rows.append(result_dict['left_row'])
        self.columns.append(result_dict['left_column'])

        self.ui.MplWidget_2.canvas.axes.clear()
        self.ui.MplWidget_2.canvas.axes.scatter(self.columns, self.rows)
        self.ui.MplWidget_2.canvas.axes.set_title('Position')
        self.ui.MplWidget_2.canvas.draw()

    def draw_brightness(self, result_dict):

        self.image_nums.append(result_dict['image_num'])
        self.right_brightness.append((result_dict['right_brightness']))
        self.left_brightness.append((result_dict['left_brightness']))
        self.brightness.append((result_dict['brightness']))

        self.ui.MplWidget.canvas.axes.clear()
        self.ui.MplWidget.canvas.axes.plot(self.image_nums, self.right_brightness)
        self.ui.MplWidget.canvas.axes.plot(self.image_nums, self.left_brightness)
        self.ui.MplWidget.canvas.axes.plot(self.image_nums, self.brightness)
        self.ui.MplWidget.canvas.axes.legend(('Right', 'Left', 'Brightness'), loc='upper right')
        self.ui.MplWidget.canvas.axes.set_title('Brightness')
        self.ui.MplWidget.canvas.draw()



    def set_result(self):
        # 有用的
        self.initialization_parameter()
        self.ui.textEdit_num.setText(str(self.result_dict['image_num']))

        self.ui.text_right_coordinate.setText(
            str(self.result_dict['right_row']) + ':' +
            str(self.result_dict['right_column'])
        )
        self.ui.text_right_brightness.setText(str(self.result_dict['right_brightness']))

        self.ui.text_left_coordinate.setText(
            str(self.result_dict['left_row']) + ':' +
            str(self.result_dict['left_column'])
        )
        self.ui.text_left_brightness.setText(str(self.result_dict['left_brightness']))

        self.ui.text_brightness.setText(str(self.result_dict['brightness']))
        self.ui.text_right_black.setText(str(self.result_dict['right_black']))
        self.ui.text_left_black.setText(str(self.result_dict['left_black']))

    # def update_graph(self):
    #     fs = 500
    #     f = random.randint(1, 100)
    #     ts = 1 / fs
    #     length_of_signal = 100
    #     t = np.linspace(0, 1, length_of_signal)
    #
    #     cosinus_signal = np.cos(2 * np.pi * f * t)
    #     sinus_signal = np.sin(2 * np.pi * f * t)
    #
    #     self.ui.MplWidget.canvas.axes.clear()
    #     self.ui.MplWidget.canvas.axes.plot(t, cosinus_signal)
    #     self.ui.MplWidget.canvas.axes.plot(t, sinus_signal)
    #     self.ui.MplWidget.canvas.axes.legend(('cosinus', 'sinus'), loc='upper right')
    #     self.ui.MplWidget.canvas.axes.set_title('Cosinus - Sinus Signals')
    #     self.ui.MplWidget.canvas.draw()

if __name__ == '__main__':
    dirname = os.path.dirname(PySide2.__file__)
    plugin_path = os.path.join(dirname, 'plugins', 'platforms')
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
    print(plugin_path)

    app = QApplication([])
    window = MainWidget()
    window.show()
    app.exec_()