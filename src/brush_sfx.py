from krita import *
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QComboBox, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent, QTimer, QPoint
from PyQt5.QtGui import QCursor, QGuiApplication
import time
import math

import numpy as np
import sounddevice as sd

from .__init__ import src_path, clamp, lerp
from .sound import sound_player
from .sound_source import WavObject, generate_from_file, generate_pen_noise, PencilSFXSource, PenSFXSource
from .filter import LowPassFilter, apply_filter, PeakFilter
from .input import InputListener, input_listener


class BrushSFXDocker(DockWidget):

    def __init__(self):
        super().__init__()
        self.mainWidget = QWidget(self)
        self.setWidget(self.mainWidget)
        self.setWindowTitle("Brush SFX")
        
        self.__sound_options = {
            "pencil-1": PencilSFXSource,
            "pen-1": PenSFXSource,
        }

        self.input_listener = input_listener
        self.player = sound_player
        self.player.startPlaying()

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(15, 20, 0, 0)
       
        # CheckBox general feature
        self.SFX_checkbox = QCheckBox("SFX", self.mainWidget)
        self.SFX_checkbox.stateChanged.connect(self.switchOnOff)
        self.SFX_checkbox.setCheckState(Qt.Checked)
        self.switchOnOff(Qt.Checked)

        # Sound Choice
        # label
        choice_label = QLabel("Sound Choice:", self.mainWidget)
        choice_label.setFixedWidth(74)
        #combobox
        self.sound_choice = QComboBox(self.mainWidget)
        self.sound_choice.addItems([key for key in self.__sound_options])
        self.sound_choice.currentTextChanged.connect(self.switchSoundChoice)
        self.sound_choice.setCurrentText("pencil-1")
        
        self.choice_layout = QHBoxLayout()
        self.choice_layout.addWidget(choice_label)
        self.choice_layout.addWidget(self.sound_choice)
        

        self.mainWidget.setLayout(self.main_layout)
        self.mainWidget.layout().addWidget(self.SFX_checkbox)
        self.mainWidget.layout().addLayout(self.choice_layout)
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

    def switchSoundChoice(self, new_text):
        self.player.setSoundSource(self.__sound_options[new_text])





Krita.instance().addDockWidgetFactory(DockWidgetFactory("brush_sfx_docker", DockWidgetFactoryBase.DockRight, BrushSFXDocker))