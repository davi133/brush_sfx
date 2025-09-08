from krita import *
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout,  QCheckBox, QOpenGLWidget, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent, QTimer, QPoint
from PyQt5.QtGui import QCursor, QGuiApplication
import time
import math

import numpy as np
import sounddevice as sd

from .__init__ import src_path, clamp, lerp
from .sound import WavObject, generate_from_file, generate_pen_noise, sound_player
from .filter import LowPassFilter, apply_filter, PeakFilter
from .input import InputListener, input_listener


class BrushSFXDocker(DockWidget):

    def __init__(self):
        super().__init__()
        self.mainWidget = QWidget(self)
        self.setWidget(self.mainWidget)
        self.setWindowTitle("Brush SFX")
        


        self.input_listener = input_listener
        self.player = sound_player
        self.player.startPlaying()

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(15, 20, 0, 0)
       

        self.lowpass_checkbox = QCheckBox("lowpass", self.mainWidget)
        self.lowpass_checkbox.stateChanged.connect(self.switchLowPass)
        
        
        self.__is_effect_on = False
        self.SFX_checkbox = QCheckBox("SFX", self.mainWidget)
        self.SFX_checkbox.stateChanged.connect(self.switchOnOff)
        self.SFX_checkbox.setCheckState(Qt.Checked)
        #
        self.switchOnOff(Qt.Checked)
        
        self.mainWidget.setLayout(self.main_layout)
        self.mainWidget.layout().addWidget(self.lowpass_checkbox)
        self.mainWidget.layout().addWidget(self.SFX_checkbox)
        print("docker initialized")

    def canvasChanged(self, canvas):
        pass

    def switchOnOff(self, state):
        if state == Qt.Checked:
            print("listening")
            QApplication.instance().installEventFilter(self.input_listener)
        else:
            print("stop listening")
            QApplication.instance().removeEventFilter(self.input_listener)

    def switchLowPass(self, state):
        pass
    
    def __del__(self):
        print("closing brush sfx docker")
        self.player.stopPlaying()



Krita.instance().addDockWidgetFactory(DockWidgetFactory("brush_sfx_docker", DockWidgetFactoryBase.DockRight, BrushSFXDocker))