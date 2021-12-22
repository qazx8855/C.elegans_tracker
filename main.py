from PySide6 import QtGui
from skimage import measure
import numpy as np
import cv2
import pandas as pd
import csv
from scipy import ndimage as ndi
import matplotlib.pyplot as plt
from skimage.feature import peak_local_max
from skimage import data, img_as_float
from skimage import io, color
import time


class record_data:
    def __init__(self):
        self.right_centre_x = []
        self.right_centre_y = []
        self.left_brightness = []
        self.right_brightness = []


class Model:

    @staticmethod
    def show_image(image):
        cv2.imshow('1', image)
        cv2.waitKey()
        cv2.destroyAllWindows()

    @staticmethod
    def transfer_16bit_to_8bit(image_path):
        image_16bit = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image_16bit is None:
            return None, None
        min_16bit = np.min(image_16bit)
        max_16bit = np.max(image_16bit)
        image_8bit = np.array(np.rint(255 * ((image_16bit - min_16bit) / (max_16bit - min_16bit))),
                              dtype=np.uint8)
        return image_16bit, image_8bit

    @staticmethod
    def flip_y(image):
        img_flip_along_y = cv2.flip(image, 1)
        return img_flip_along_y

    @staticmethod
    def blurleft_and_thresh(image_8bit):
        blurleft = cv2.GaussianBlur(image_8bit, (11, 11), 0)
        # threshold the image to reveal light regions in the
        # blurleft image
        thresh = cv2.threshold(blurleft, 50, 255, cv2.THRESH_BINARY)[1]
        return thresh

    @staticmethod
    def find_right_centre(thresh):
        m = cv2.moments(thresh)
        x = int(m['m10'] / m['m00'])
        y = int(m['m01'] / m['m00'])
        return x, y

    def quick_find_blob(self, image_8bit):

        thresh = self.blurleft_and_thresh(image_8bit)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        m00 = []
        centres = []
        for c in contours:
            # calculate moments for each contour
            moments = cv2.moments(c)
            m00.append(moments['m00'])
            if moments['m00'] != 0:
                centres.append((int(moments['m10'] / moments['m00']), int(moments['m01'] / moments['m00'])))

        m = cv2.moments(contours[m00.index(max(m00))])
        right_centre_x = int(m['m10'] / m['m00'])
        right_centre_y = int(m['m01'] / m['m00'])
        return right_centre_x, right_centre_y

    @staticmethod
    def image_bright(image, alpha=3, beta=0):
        image_bright = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        return image_bright

    @staticmethod
    def find_left_centre(column, row, bias_row=0, bias_column=0):
        left_centre_row = row + bias_row
        left_centre_column = column - 255 + bias_column
        return left_centre_row, left_centre_column

    def surrender_value_compare(self, image, row, column, surrender):
        value = image[row][column]
        for i in range(0, 2 * surrender + 1):
            if 0 < row - surrender + i < image.shape[0] and 0 < column - surrender \
                    and column + surrender < image.shape[1]:
                if value < image[row - surrender + i][column - surrender] \
                        or value < image[row - surrender + i][column + surrender]:
                    return False
        for i in range(1, 2 * surrender):
            if 0 < row - surrender and row + surrender < image.shape[0] \
                    and 0 < column - surrender + i < image.shape[1]:
                if value < image[row - surrender][column - surrender + i] \
                        or value < image[row + surrender][column - surrender + i]:
                    return False
        return True

    def surrender(self, image, row, column, circle):
        for i in range(1, int(circle) + 1):
            if not self.surrender_value_compare(image, row, column, i):
                return False
        return True

    def find_peak_point(self, image, circle=6, ratio=0.4):
        centres = []
        image_max = np.max(image)
        start = int(image.shape[1] / 2)
        end = int(image.shape[0])
        for column in range(start, end):
            for row in range(0, image.shape[1]):
                if image[row][column] > (ratio * image_max):
                    if self.surrender(image, row, column, circle):
                        centres.append([row, column])

        return centres

    def draw_rectangle(self, image, column, row, label_text, radius=5, text_place=5):
        # 框一半边长
        # 标签离框的距离
        cv2.rectangle(image, (int(column - radius), int(row - radius)),
                      (int(column + radius), int(row + radius)), 255)
        cv2.putText(image, label_text, (column - radius, row - radius - text_place),
                    cv2.FONT_HERSHEY_COMPLEX, 0.5, 255, 1)

    @staticmethod
    def right_black(image, black_bias=0):
        right_image = image[:240, 388:450]
        minimum = np.min(right_image)
        if minimum < 32862:
            return 32862
        return minimum + black_bias

    @staticmethod
    def left_black(image, black_bias=0):
        left_image = image[:240, 30:120]
        minimum = np.min(left_image)
        if minimum < 32862:
            return 32862
        return minimum + black_bias

    def find_max_brightness(self, image, centres):
        max_brightness = 0
        max_row = 0
        max_column = 0
        for centre in centres:
            if image[centre[0]][centre[1]] > max_brightness:
                max_brightness = image[centre[0]][centre[1]]
                max_row = centre[0]
                max_column = centre[1]

        return max_brightness, max_row, max_column

    def mean_in_array(self, array):
        mean = array[np.nonzero(array)].mean()
        return mean

    def right_array(self, image, row, column, radius, ratio, black):
        right_light_array = image[row - radius: row + radius + 1, column - radius: column + radius + 1]
        right_light_array -= black

        right_light_array = np.where(right_light_array < 0, 0, right_light_array)
        right_light_array_max = np.max(right_light_array)

        right_light_array = np.where(right_light_array > (right_light_array_max * ratio), right_light_array, 0)
        return right_light_array

    def left_array(self, image, left_centre_row, left_centre_column, right_light_array, radius, black):
        right_light_array_shape = np.where(right_light_array > 1, 1, 0)
        raw_left_light_array = image[left_centre_row - radius: left_centre_row + radius + 1,
                               left_centre_column - radius: left_centre_column + radius + 1]
        left_light_array = raw_left_light_array * right_light_array_shape
        left_light_array -= black
        left_light_array = np.where(left_light_array < 0, 0, left_light_array)
        return left_light_array

    def calculate_brightness(self, image, image_num, row, column, right_black, left_black, radius=5, ratio=0.6,
                             row_bias=0,
                             column_bias=0):
        left_row, left_column = self.find_left_centre(column, row, row_bias, column_bias)

        right_light_array = self.right_array(image, row, column, radius, ratio, right_black)
        print(right_light_array)
        left_light_array = \
            self.left_array(image, left_row, left_column, right_light_array, radius, left_black)
        print(left_light_array)
        right_brightness = self.mean_in_array(right_light_array)
        left_brightness = self.mean_in_array(left_light_array)
        result_dict = {
            'num': image_num,
            'right_row': row, 'right_column': column, 'right_brightness': right_brightness,
            'left_row': left_row, 'left_column': left_column, 'left_brightness': left_brightness,
            'brightness': left_brightness / right_brightness
        }
        return result_dict

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
        return dataframe

    def rotate_picture(self, image, angle):
        (h, w) = image.shape[:2]
        (cX, cY) = (w // 2, h // 2)
        m = cv2.getRotationMatrix2D((cX, cY), angle, 1.0)
        rotated = cv2.warpAffine(image, m, (w, h))
        return rotated

    def label(self, image, centres, label_radius, bias_row, bias_column):
        for centre in centres:
            label_text = str(centres.index(centre))
            self.draw_rectangle(image, centre[1], centre[0], label_text, label_radius)

            left_row, left_column = self.find_left_centre(centre[1], centre[0], bias_row, bias_column)
            self.draw_rectangle(image, left_column, left_row, label_text, label_radius)
        return image

    def control(self, image_path, current_image):
        image_path_n = image_path + f'{current_image:04}' + '.tif'
        image_16bit, image_8bit = self.model.transfer_16bit_to_8bit(image_path_n)
        if image_16bit is None:
            return None

        image_bright = self.model.image_bright(image_8bit, alpha=3, beta=0)  # 用户输入
        # model.show_image(image_bright)

        centres = self.model.find_peak_point(image_8bit, circle=6, ratio=0.4)
        # print(centres)

        # centres = peak_local_max(image_8bit, num_peaks=20, exclude_border=2)
        # print(image_8bit.shape[0])

        bias_row = 0
        bias_column = 5
        label_radius = 7
        for centre in centres:
            label_text = str(centres.index(centre))
            self.model.draw_rectangle(image_bright, centre[1], centre[0], label_text, label_radius)

            left_row, left_column = self.model.find_left_centre(centre[1], centre[0], bias_row, bias_column)
            self.model.draw_rectangle(image_bright, left_column, left_row, label_text, label_radius)

        radius = label_radius
        ratio = 0.5
        max_brightness, max_row, max_column = self.model.find_max_brightness(image_8bit, centres)
        self.dataframe = self.model.calculate_brightness(image_16bit, self.dataframe, max_row, max_column,
                                                         radius, ratio, bias_row, bias_column)
        print(self.dataframe)
        self.model.show_image(image_bright)

        self.dataframe.to_csv('data7.csv', sep=',', encoding='utf-8')

    def cv2QPix(self, img):
        # cv 图片转换成 qt图片
        qt_img = QtGui.QImage(img.data,  # 数据源
                              img.shape[1],  # 宽度
                              img.shape[0],  # 高度
                              img.shape[1],  # 行字节数
                              QtGui.QImage.Format_Grayscale8)
        return QtGui.QPixmap.fromImage(qt_img)

    def open_image(self, ui, parameter_dict, num, image_path, flip):
        if image_path != '':
            image_path_n = image_path + '/' + f'{num:04}' + '.tif'
            image_16bit, image_8bit = self.transfer_16bit_to_8bit(image_path_n)
            if image_16bit is None:
                print("wrong1")
            if flip:
                image_8bit = self.flip_y(image_8bit)
                image_16bit = self.flip_y(image_16bit)

            image_bright = self.image_bright(image_8bit, parameter_dict['alpha'], parameter_dict['beta'])

            return image_16bit, image_8bit, image_bright

        else:
            print("wrong")

    def set_parameter(self, ui, parameter_dict):
        parameter_dict['alpha'] = float(ui.textEdit_alpha.toPlainText())
        parameter_dict['beta'] = float(ui.textEdit_beta.toPlainText())

        parameter_dict['peak_ratio'] = float(ui.textEdit_peak_ratio.toPlainText())
        parameter_dict['peak_circle'] = int(ui.textEdit_peak_circle.toPlainText())

        parameter_dict['right_ratio'] = float(ui.textEdit_right_ratio.toPlainText())
        parameter_dict['right_circle'] = int(ui.textEdit_right_circle.toPlainText())

        parameter_dict['row_bias'] = int(ui.textEdit_row_bias.toPlainText())
        parameter_dict['column_bias'] = int(ui.textEdit_column_bias.toPlainText())

        parameter_dict['left_ratio'] = float(ui.textEdit_left_ratio.toPlainText())
        parameter_dict['left_circle'] = int(ui.textEdit_left_circle.toPlainText())

        parameter_dict['right_black_bias'] = int(ui.textEdit_right_black_bias.toPlainText())
        parameter_dict['left_black_bias'] = int(ui.textEdit_left_black_bias.toPlainText())

    def set_black(self, ui, parameter_dict, image_16bit):
        parameter_dict['right_black'] = self.right_black(
            image_16bit,
            parameter_dict['right_black_bias']
        )
        parameter_dict['left_black'] = self.left_black(
            image_16bit,
            parameter_dict['left_black_bias']
        )

        print(parameter_dict['left_black'], parameter_dict['right_black'])

        ui.text_right_black.setText(str(parameter_dict['right_black']))
        ui.text_left_black.setText(str(parameter_dict['left_black']))

    def process_image(self, ui, parameter_dict, image_num, image_16bit, image_8bit, image_bright):
        self.set_parameter(ui, parameter_dict)
        self.set_black(ui, parameter_dict, image_16bit)

        right_centres = self.find_peak_point(
            image_8bit, parameter_dict['peak_circle'], parameter_dict['peak_ratio'])

        image_bright = self.label(
            image_bright, right_centres,
            parameter_dict['label_radius'],
            parameter_dict['row_bias'],
            parameter_dict['column_bias']
        )
        ui.label_image.setPixmap(self.cv2QPix(image_bright))
        ui.textEdit_num.setText(str(image_num))
        max_brightness, max_row, max_column = self.find_max_brightness(image_8bit, right_centres)
        result_dict = self.calculate_brightness(
            image_16bit, image_num, max_row, max_column,
            parameter_dict['right_black'], parameter_dict['left_black'],
            parameter_dict['right_circle'], parameter_dict['right_ratio'],
            parameter_dict['row_bias'],
            parameter_dict['column_bias']
        )
        return result_dict

    def set_result(self, ui, result_dict):
        ui.text_right_coordinate.setText(
            str(result_dict['right_row']) + ':' +
            str(result_dict['right_column'])
        )
        ui.text_right_brightness.setText(str(result_dict['right_brightness']))

        ui.text_left_coordinate.setText(
            str(result_dict['left_row']) + ':' +
            str(result_dict['left_column'])
        )
        ui.text_left_brightness.setText(str(result_dict['left_brightness']))

        ui.text_brightness.setText(str(result_dict['brightness']))



class Controller:
    def __init__(self):
        self.model = Model()
        self.dataframe = pd.DataFrame(
            columns=['Right_row', 'Right_column', 'Right_brightness', 'Left_row', 'Left_column', 'Left_brightness',
                     'Brightness'])

    def control(self):
        image_path = 'D:/082516_AVAAVE-G3-13/'
        i = 0
        while True:
            image_path_n = image_path + f'{i:04}' + '.tif'
            image_16bit, image_8bit = self.model.transfer_16bit_to_8bit(image_path_n)
            if image_16bit is None:
                break

            image_bright = self.model.image_bright(image_8bit, alpha=3, beta=0)  # 用户输入
            # model.show_image(image_bright)

            centres = self.model.find_peak_point(image_8bit, circle=6, ratio=0.4)
            # print(centres)

            # centres = peak_local_max(image_8bit, num_peaks=20, exclude_border=2)
            # print(image_8bit.shape[0])

            bias_row = 0
            bias_column = 5
            label_radius = 7
            for centre in centres:
                label_text = str(centres.index(centre))
                self.model.draw_rectangle(image_bright, centre[1], centre[0], label_text, label_radius)

                left_row, left_column = self.model.find_left_centre(centre[1], centre[0], bias_row, bias_column)
                self.model.draw_rectangle(image_bright, left_column, left_row, label_text, label_radius)

            radius = label_radius
            ratio = 0.5
            max_brightness, max_row, max_column = self.model.find_max_brightness(image_8bit, centres)
            result_dict = self.model.calculate_brightness(image_16bit, max_row, max_column,
                                                          radius, ratio, bias_row, bias_column)
            self.dataframe = self.model.write_csv(result_dict, self.dataframe)
            print(self.dataframe)
            self.model.show_image(image_bright)

            self.dataframe.to_csv('data6.csv', sep=',', encoding='utf-8')
            i += 1


if __name__ == '__main__':
    controller = Controller()
    controller.control()

    print(time.process_time())
    print(time.perf_counter())
