from krita import *
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QComboBox, QLabel, QDialog, QSlider
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

        _volume_setting = Krita.instance().readSetting("BrushSfxGroup", "volume", "100")
        if _volume_setting.isdigit():
            _volume_setting = clamp(int(_volume_setting), 0, 100)
        else:
            _volume_setting = 50
        self.changeVolume(int(_volume_setting))


    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction("sfxConfig", "Brush SFX", "tools")
        action.triggered.connect(self.openConfig)

    def __createDialog(self):
        self.dialogWidget.setWindowFlag(Qt.WindowStaysOnTopHint)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 20, 15, 20)

        self.dialogWidget.setWindowTitle("Brush SFX")

        # CheckBox general feature
        self.SFX_checkbox = QCheckBox("SFX", self.dialogWidget)
        self.SFX_checkbox.stateChanged.connect(self.switchOnOff)

        # Volume slider
        # label
        volume_label = QLabel("Volume:", self.dialogWidget)
        volume_label.setFixedWidth(43)
        # slider
        self.volume_slider = QSlider(self.dialogWidget)
        self.volume_slider.setTracking(True)
        self.volume_slider.setOrientation(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.valueChanged.connect(self.changeVolume)
        # value label 
        self.volume_value_label = QLabel("100", self.dialogWidget)
        self.volume_value_label.setFixedWidth(20)
        # layout
        volume_slider_layout = QHBoxLayout()
        volume_slider_layout.addWidget(self.volume_slider)
        volume_slider_layout.addWidget(self.volume_value_label)
        

        volume_layout = QVBoxLayout()
        volume_layout.addWidget(volume_label)
        volume_layout.addLayout(volume_slider_layout)

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
        self.dialogWidget.layout().addLayout(volume_layout)
        self.dialogWidget.layout().addLayout(choice_layout)
    
    def setupDialogData(self):
        _checked_state_setting = Krita.instance().readSetting("BrushSfxGroup", "brush_sfx_on", "True")
        _qt_checked_state = Qt.Checked if _checked_state_setting != "False" else Qt.Unchecked
        self.SFX_checkbox.setCheckState(_qt_checked_state)

        _volume_setting = Krita.instance().readSetting("BrushSfxGroup", "volume", "50")
        if _volume_setting.isdigit():
            _volume_setting = clamp(int(_volume_setting), 0, 100)
        else:
            _volume_setting = 50
        self.volume_slider.setValue(int(_volume_setting))

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
    
    def changeVolume(self, value: int):
        Krita.instance().writeSetting("BrushSfxGroup", "volume", str(value))
        self.volume_value_label.setText(str(value))
        volume = int(value)/100.0
        self.player.setVolume(volume)

    def switchSoundChoice(self, new_text):
        Krita.instance().writeSetting("BrushSfxGroup", "sound_choice", new_text)
        self.player.setSoundSource(self.__sound_options[new_text])
    
    

    def openConfig(self):
        self.setupDialogData()
        self.dialogWidget.show()     

# And add the extension to Krita's list of extensions:
exten = BrushSFXExtension(Krita.instance())
Krita.instance().addExtension(exten)
