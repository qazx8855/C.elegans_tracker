
import os
from datetime import datetime
from PySide2 import QtWidgets, QtCore, QtGui
import pandas as pd
from PySide2.QtCore import *

from skimage import io

# import cv2
import numpy as np
import time
from pycromanager import Bridge
from matplotlib import pyplot as plt

with Bridge() as bridge:
    # get object representing micro-manager core
    core = bridge.get_core()

    #### Calling core functions ###
    exposure = core.get_exposure()

    #### Setting and getting properties ####
    # Here we set a property of the core itself, but same code works for device properties
    auto_shutter = core.get_property('Core', 'AutoShutter')
    core.set_property('Core', 'AutoShutter', 0)
    stage = core.get_xy_stage_position()

    def snap_image():
        core.snap_image()
        tagged_image = core.get_tagged_image()
        image = np.reshape(tagged_image.pix,
                           newshape=[tagged_image.tags['Height'], tagged_image.tags['Width']])


        image = np.flip(image, 1)

        image = np.rot90(image, 1)

        return image

    print(snap_image())

    stage_p = core.get_xy_stage_position()
    stage_x = stage_p.get_x()
    stage_y = stage_p.get_y()
    print(stage_x, stage_y)

    stage1 = core.get_xy_stage_device()
    core.set_xy_position(stage1, stage_x, stage_y+100)

    stage_p = core.get_xy_stage_position()
    stage_x = stage_p.get_x()
    stage_y = stage_p.get_y()
    print(stage_x, stage_y)