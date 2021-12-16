import os

from scipy import ndimage as ndi
import matplotlib.pyplot as plt
from skimage.feature import peak_local_max
from skimage import data, img_as_float
from skimage import io, color
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

import re

# img = io.imread("D:/082516_AVAAVE-G3-13/0000.tif")  # 同 gray = color.rgb2gray(img) 的结果
# image_16bit = cv2.imread("D:/082516_AVAAVE-G3-13/0000.tif", cv2.IMREAD_UNCHANGED)
# min_16bit = np.min(image_16bit)
# max_16bit = np.max(image_16bit)
# image_8bit = np.array(np.rint(255 * ((image_16bit - min_16bit) / (max_16bit - min_16bit))),
#                       dtype=np.uint8)
# img_flip_along_y = cv2.flip(image_8bit, 1)
# plt.imshow(img_flip_along_y)
# # M = cv2.getRotationMatrix2D((255, 255), 45, 1.0)
# # rotated = cv2.warpAffine(img, M, (511, 511))
# cv2.imshow("Rotated by -90 Degrees", img_flip_along_y)
# cv2.waitKey()
# cv2.destroyAllWindows()
# # print(rotated)

# cv2.imshow("Rotated by 45 Degrees", rotated)
# coordinates = peak_local_max(img, min_distance=100)
# print(coordinates)
# a = np.array([0, 1, 2, 3, 0])
# print(a)
# b = np.array([0, 1, 1, 0, 0])
# d = 5
# c = b - d
# print(c)
# print(time.perf_counter())

image_path = "D:/082516_AVAAVE-G3-13/0015.tif"
head, tail = os.path.split(image_path)
regex = re.compile(r'\d+')

if bool(re.search(r'\d', tail)):
    num = int(max(regex.findall(tail)))

a = 1

