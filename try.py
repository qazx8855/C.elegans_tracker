import os
import re
from PySide6 import QtWidgets, QtCore
from main import *
from PySide6.QtCore import *
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import *
import time
from PySide6.QtGui import *
from PySide6 import QtGui
import sys


class Worker(QObject):
    """线程类"""
    image_signal = Signal(object)
    finished = Signal()
    def __init__(self):
        super(Worker, self).__init__()

        self.ui = None
        self.image_path = None
        self.parameter_dict = None
        self.model = Model()

        self.image_16bit = None
        self.image_8bit = None
        self.image_bright = None

        self.result_dict = {}

        self.start = None
        self.end = None

        self.flip = False

    def set_value(self, ui, image_path, parameter_dict, start, end, flip):
        self.ui = ui
        self.image_path = image_path
        self.parameter_dict = parameter_dict

        self.result_dict = {}

        self.start = start
        self.end = end

        self.flip = flip

    def open_image(self, image_num):
        self.image_16bit, self.image_8bit, self.image_bright = \
            self.model.open_image(self.ui, self.parameter_dict, image_num, self.image_path, self.flip)
        self.model.set_parameter(self.ui, self.parameter_dict)
        self.result_dict = self.model.process_image(self.ui, self.parameter_dict, image_num, self.image_16bit,
                                                    self.image_8bit,
                                                    self.image_bright)

    def run(self):
        for i in range(self.start, self.end + 1):
            self.open_image(i)
            self.image_signal.emit(self.result_dict)
            time.sleep(0.2)


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.start = None
        qfile = QFile('ui.ui')
        qfile.open(QFile.ReadOnly)
        qfile.close()
        self.cwd = os.getcwd()  # 获取当前程序文件位置
        # 从UI定义中动态创建一个相应的窗口对象
        self.ui = QUiLoader().load(qfile)

        # self.ui = gui.Ui_Form()  # 实例化UI对象
        # self.ui.setupUi(self)  # 初始化

        self.model = Model()

        self.image_name = ''
        self.image_path = ''

        self.image_num = 0
        self.image_8bit = None
        self.image_16bit = None
        self.image_bright = None

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



        # 信号处理
        self.ui.button_select_file.clicked.connect(self.button_select_file)
        self.ui.button_next.clicked.connect(self.button_next)
        self.ui.button_last.clicked.connect(self.button_last)
        self.ui.button_go.clicked.connect(self.button_go)
        self.ui.button_run.clicked.connect(self.button_run)
        self.ui.button_refresh.clicked.connect(self.button_refresh)

        self.ui.checkbox_mirror_symmetry.stateChanged.connect(self.checkbox_mirror_symmetry)

        self.ui.text_file_path.setText(self.image_path)

    # def cv2QPix(self, img):
    #     # cv 图片转换成 qt图片
    #     qt_img = QtGui.QImage(img.data,  # 数据源
    #                           img.shape[1],  # 宽度
    #                           img.shape[0],  # 高度
    #                           img.shape[1],  # 行字节数
    #                           QtGui.QImage.Format_Grayscale8)
    #     return QtGui.QPixmap.fromImage(qt_img)

    def open_image(self, image_num):
        self.image_16bit, self.image_8bit, self.image_bright = \
            self.model.open_image(self.ui, self.parameter_dict, image_num, self.image_path, self.flip)
        self.model.set_parameter(self.ui, self.parameter_dict)
        self.result_dict = self.model.process_image(self.ui, self.parameter_dict, image_num, self.image_16bit,
                                                    self.image_8bit,
                                                    self.image_bright)
        if self.result_dict != {}:
            self.model.set_result(self.ui, self.result_dict)

        # if self.image_path != '':
        #     image_path_n = self.image_path + '/' + f'{num:04}' + '.tif'
        #     self.image_16bit, self.image_8bit = self.model.transfer_16bit_to_8bit(image_path_n)
        #     if self.image_16bit is None:
        #         return False
        #     if self.flip:
        #         self.image_8bit = self.model.flip_y(self.image_8bit)
        #         self.image_16bit = self.model.flip_y(self.image_16bit)
        #
        #     self.image_bright = self.model.image_bright(self.image_8bit, alpha=3, beta=0)
        #     self.process_image()
        #     self.ui.label_image.setPixmap(self.cv2QPix(self.image_bright))
        #     self.ui.text_num.setText(str(self.image_num))
        #     return True

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

    # def set_parameter(self):
    #     self.parameter_dict['alpha'] = float(self.ui.textEdit_alpha.toPlainText())
    #     self.parameter_dict['beta'] = float(self.ui.textEdit_beta.toPlainText())
    #
    #     self.parameter_dict['peak_ratio'] = float(self.ui.textEdit_peak_ratio.toPlainText())
    #     self.parameter_dict['peak_circle'] = int(self.ui.textEdit_peak_circle.toPlainText())
    #
    #     self.parameter_dict['right_ratio'] = float(self.ui.textEdit_right_ratio.toPlainText())
    #     self.parameter_dict['right_circle'] = int(self.ui.textEdit_right_circle.toPlainText())
    #
    #     self.parameter_dict['row_bias'] = int(self.ui.textEdit_row_bias.toPlainText())
    #     self.parameter_dict['column_bias'] = int(self.ui.textEdit_column_bias.toPlainText())
    #
    #     self.parameter_dict['left_ratio'] = float(self.ui.textEdit_left_ratio.toPlainText())
    #     self.parameter_dict['left_circle'] = int(self.ui.textEdit_left_circle.toPlainText())
    #
    #     self.parameter_dict['right_black_bias'] = int(self.ui.textEdit_right_black_bias.toPlainText())
    #     self.parameter_dict['left_black_bias'] = int(self.ui.textEdit_left_black_bias.toPlainText())
    #
    # def set_black(self):
    #     self.set_parameter()
    #     self.parameter_dict['right_black'] = self.model.right_black(
    #         self.image_16bit,
    #         self.parameter_dict['right_black_bias']
    #     )
    #     self.parameter_dict['left_black'] = self.model.left_black(
    #         self.image_16bit,
    #         self.parameter_dict['left_black_bias']
    #     )
    #     print(self.parameter_dict['left_black'], self.parameter_dict['right_black'])
    #     self.ui.text_right_black.setText(str(self.parameter_dict['right_black']))
    #     self.ui.text_left_black.setText(str(self.parameter_dict['left_black']))
    #
    # def process_image(self):
    #     self.set_parameter()
    #     self.set_black()
    #
    #     right_centres = self.model.find_peak_point(
    #         self.image_8bit, self.parameter_dict['peak_circle'], self.parameter_dict['peak_ratio'])
    #
    #     self.image_bright = self.model.label(
    #         self.image_bright, right_centres,
    #         self.parameter_dict['label_radius'],
    #         self.parameter_dict['row_bias'],
    #         self.parameter_dict['column_bias']
    #     )
    #
    #     max_brightness, max_row, max_column = self.model.find_max_brightness(self.image_8bit, right_centres)
    #     self.result_dict = self.model.calculate_brightness(
    #         self.image_16bit, self.image_num, max_row, max_column,
    #         self.parameter_dict['right_black'], self.parameter_dict['left_black'],
    #         self.parameter_dict['right_circle'], self.parameter_dict['right_ratio'],
    #         self.parameter_dict['row_bias'],
    #         self.parameter_dict['column_bias']
    #     )
    #     self.results.append(self.result_dict)
    #     self.set_result()
    #
    # def set_result(self):
    #     self.ui.text_right_coordinate.setText(
    #         str(self.result_dict['right_row']) + ':' +
    #         str(self.result_dict['right_column'])
    #     )
    #     self.ui.text_right_brightness.setText(str(self.result_dict['right_brightness']))
    #
    #     self.ui.text_left_coordinate.setText(
    #         str(self.result_dict['left_row']) + ':' +
    #         str(self.result_dict['left_column'])
    #     )
    #     self.ui.text_left_brightness.setText(str(self.result_dict['left_brightness']))
    #
    #     self.ui.text_brightness.setText(str(self.result_dict['brightness']))
    #     self.set_black()

    def process_images(self, start, end=0):
        self.results = []
        self.image_num = start - 1
        for i in range(5):
            self.button_next()
            time.sleep(1)
            # if self.open_image(self.image_num) is False:
            #     break

            # if end != 0:
            #     if start > end:
            #         break

    def set_results(self, result_dict):
        if self.result_dict != {}:
            self.model.set_result(self.ui, self.result_dict)
        self.model.set_result(self.ui, result_dict)

    def button_select_file(self):
        image_path_name, _ = QFileDialog.getOpenFileName(self, 'Select image', '', 'Image files(*.tif)')
        print(image_path_name)
        self.image_path, self.image_name = os.path.split(image_path_name)
        print(self.image_path, self.image_name)
        self.ui.text_file_path.setText(self.image_path)

        if self.image_path == '':
            self.image_path = QFileDialog.getExistingDirectory(self, 'Select image')
            self.ui.text_file_path.setText(self.image_path)
            print(self.image_path)
            print('\nCancel')

        regex = re.compile(r'\d+')
        if bool(re.search(r'\d', self.image_name)):
            self.image_num = int(max(regex.findall(self.image_name)))
            print(self.image_num)
        self.open_image(self.image_num)

    def button_next(self):
        self.image_num += 1
        self.open_image(self.image_num)

    def button_last(self):
        self.image_num -= 1
        self.open_image(self.image_num)

    def button_go(self):
        self.image_num = int(self.ui.textEdit_num.toPlainText())
        self.open_image(self.image_num)

    def button_run(self):
        self.worker = Worker()
        self.worker.image_signal.connect(self.set_results)
        start = int(self.ui.textEdit_start.toPlainText())
        end = int(self.ui.textEdit_end.toPlainText())
        self.worker.set_value(self.ui, self.image_path, self.parameter_dict, start, end, self.flip)

        self.worker.start()

    def button_refresh(self):
        self.open_image(self.image_num)

    def checkbox_mirror_symmetry(self):
        self.flip = not self.flip
        self.open_image(self.image_num)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    widget = MyWidget()
    # widget.show()
    widget.ui.show()
    sys.exit(app.exec())
