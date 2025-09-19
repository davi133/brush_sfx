from krita import *
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QComboBox, QLabel, QDialog
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent, QTimer, QPoint
from PyQt5.QtGui import QCursor, QGuiApplication
import time
import math

import numpy as np
import sounddevice as sd

from .utils import clamp, lerp
from .sound import sound_player
from .sound_source import WavObject, generate_from_file, generate_pen_noise, PencilSFXSource, PenSFXSource
from .filter import LowPassFilter, apply_filter, PeakFilter
from .input import InputListener, input_listener

class BrushSFXExtension(Extension):

    def __init__(self, parent):
        super().__init__(parent)
        print("initializing action")
        self.setObjectName('brush_sfx_extension')

        self.dialogWidget = QDialog()
        self.SFX_checkbox = None
        self.sound_choice_cb = None

        self.__sound_options = {
            "pencil-1": PencilSFXSource,
            "pen-1": PenSFXSource,
        }
        self.input_listener = input_listener
        self.player = sound_player
        self.player.startPlaying()
        
        self.__createDialog()

        _checked_state_setting = Krita.instance().readSetting("BrushSfxGroup", "brush_sfx_on", "True")
        _qt_checked_state = Qt.Checked if _checked_state_setting != "False" else Qt.Unchecked
        self.switchOnOff(_qt_checked_state)

        _sound_choice_setting = Krita.instance().readSetting("BrushSfxGroup", "sound_choice", "pencil-1")
        if not _sound_choice_setting in self.__sound_options:
            _sound_choice_setting = "pencil-1"
        self.switchSoundChoice(_sound_choice_setting)

        self._the_window = None


    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction("sfxConfig", "Brush SFX", "tools")
        action.triggered.connect(self.openConfig)

        action2 = window.createAction("sfxTest", "TestBrush", "tools")
        action2.triggered.connect(self.test_brush)

    def aaaa(self):
        print("view changed")

    def test_brush(self):
        print("nothin to test")
        


    def __createDialog(self):
        self.dialogWidget.setWindowFlag(Qt.WindowStaysOnTopHint)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 20, 15, 20)

        self.dialogWidget.setWindowTitle("Brush SFX")

        # CheckBox general feature
        self.SFX_checkbox = QCheckBox("SFX", self.dialogWidget)
        self.SFX_checkbox.stateChanged.connect(self.switchOnOff)

        # Sound Choice
        # label
        choice_label = QLabel("Sound Choice:", self.dialogWidget)
        choice_label.setFixedWidth(74)
        #combobox
        self.sound_choice_cb = QComboBox(self.dialogWidget)
        self.sound_choice_cb.addItems([key for key in self.__sound_options])
        self.sound_choice_cb.currentTextChanged.connect(self.switchSoundChoice)

        #layout
        choice_layout = QHBoxLayout()
        choice_layout.addWidget(choice_label)
        choice_layout.addWidget(self.sound_choice_cb)

        self.dialogWidget.setLayout(main_layout)
        self.dialogWidget.layout().addWidget(self.SFX_checkbox)
        self.dialogWidget.layout().addLayout(choice_layout)
    
    def setupDialog(self):
        _checked_state_setting = Krita.instance().readSetting("BrushSfxGroup", "brush_sfx_on", "True")
        _qt_checked_state = Qt.Checked if _checked_state_setting != "False" else Qt.Unchecked
        self.SFX_checkbox.setCheckState(_qt_checked_state)

        _sound_choice_setting = Krita.instance().readSetting("BrushSfxGroup", "sound_choice", "pencil-1")
        if not _sound_choice_setting in self.__sound_options:
            _sound_choice_setting = "pencil-1"
        self.sound_choice_cb.setCurrentText(_sound_choice_setting)

    def switchOnOff(self, state):
        if state == Qt.Checked:
            Krita.instance().writeSetting("BrushSfxGroup", "brush_sfx_on", "True")
            self.input_listener.startListening()
        else:
            Krita.instance().writeSetting("BrushSfxGroup", "brush_sfx_on", "False")
            self.input_listener.stopListening()
    
    def switchSoundChoice(self, new_text):
        Krita.instance().writeSetting("BrushSfxGroup", "sound_choice", new_text)
        self.player.setSoundSource(self.__sound_options[new_text])

    def openConfig(self):
        self.setupDialog()
        self.dialogWidget.show()     

# And add the extension to Krita's list of extensions:
exten = BrushSFXExtension(Krita.instance())
Krita.instance().addExtension(exten)
