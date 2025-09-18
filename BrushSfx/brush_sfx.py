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

        self.__sound_options = {
            "pencil-1": PencilSFXSource,
            "pen-1": PenSFXSource,
        }
        self.input_listener = input_listener
        self.player = sound_player
        self.player.startPlaying()

        _checked_state_setting = Krita.instance().readSetting("BrushSfxGroup", "brush_sfx_on", "True")
        _qt_checked_state = Qt.Checked if _checked_state_setting != "False" else Qt.Unchecked
        self.switchOnOff(_qt_checked_state)

        _sound_choice_setting = Krita.instance().readSetting("BrushSfxGroup", "sound_choice", "pencil-1")
        if not _sound_choice_setting in self.__sound_options:
            _sound_choice_setting = "pencil-1"
        self.switchSoundChoice(_sound_choice_setting)

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction("sfxConfig", "Brush SFX", "tools")
        action.triggered.connect(self.openConfig)

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
        print(f"the value was successfully printed")
        
        dialogWidget = QDialog()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 20, 15, 20)

        
        dialogWidget.setWindowTitle("Brush SFX") 
        
        # CheckBox general feature
        SFX_checkbox = QCheckBox("SFX", dialogWidget)
        SFX_checkbox.stateChanged.connect(self.switchOnOff)
        _checked_state_setting = Krita.instance().readSetting("BrushSfxGroup", "brush_sfx_on", "True")
        _qt_checked_state = Qt.Checked if _checked_state_setting != "False" else Qt.Unchecked
        SFX_checkbox.setCheckState(_qt_checked_state)
        
        # Sound Choice
        # label
        choice_label = QLabel("Sound Choice:", dialogWidget)
        choice_label.setFixedWidth(74)
        #combobox
        sound_choice_cb = QComboBox(dialogWidget)
        sound_choice_cb.addItems([key for key in self.__sound_options])
        sound_choice_cb.currentTextChanged.connect(self.switchSoundChoice)
        _sound_choice_setting = Krita.instance().readSetting("BrushSfxGroup", "sound_choice", "pencil-1")
        if not _sound_choice_setting in self.__sound_options:
            _sound_choice_setting = "pencil-1"
        sound_choice_cb.setCurrentText(_sound_choice_setting)
        #layout
        choice_layout = QHBoxLayout()
        choice_layout.addWidget(choice_label)
        choice_layout.addWidget(sound_choice_cb)

        dialogWidget.setLayout(main_layout)
        dialogWidget.layout().addWidget(SFX_checkbox)
        dialogWidget.layout().addLayout(choice_layout)
        dialogWidget.exec_()       

# And add the extension to Krita's list of extensions:
exten = BrushSFXExtension(Krita.instance())
Krita.instance().addExtension(exten)

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
        checked_state = Krita.instance().readSetting("BrushSfxGroup", "brush_sfx_on", "True")
        qt_checked_state = Qt.Checked if checked_state != "False" else Qt.Unchecked
        self.SFX_checkbox.setCheckState(qt_checked_state)
        self.switchOnOff(qt_checked_state)

        # Sound Choice
        # label
        choice_label = QLabel("Sound Choice:", self.mainWidget)
        choice_label.setFixedWidth(74)
        #combobox
        self.sound_choice = QComboBox(self.mainWidget)
        self.sound_choice.addItems([key for key in self.__sound_options])
        self.sound_choice.currentTextChanged.connect(self.switchSoundChoice)
        sound_choice_setting = Krita.instance().readSetting("BrushSfxGroup", "sound_choice", "pencil-1")
        if not sound_choice_setting in self.__sound_options:
            sound_choice_setting = "pencil-1"
        self.sound_choice.setCurrentText(sound_choice_setting)
        self.switchSoundChoice(sound_choice_setting)
        
        self.choice_layout = QHBoxLayout()
        self.choice_layout.addWidget(choice_label)
        self.choice_layout.addWidget(self.sound_choice)
        

        self.mainWidget.setLayout(self.main_layout)
        self.mainWidget.layout().addWidget(self.SFX_checkbox)
        self.mainWidget.layout().addLayout(self.choice_layout)

    def canvasChanged(self, canvas):
        pass

    def switchOnOff(self, state):
        return
        if state == Qt.Checked:
            Krita.instance().writeSetting("BrushSfxGroup", "brush_sfx_on", "True")
            self.input_listener.startListening()
        else:
            Krita.instance().writeSetting("BrushSfxGroup", "brush_sfx_on", "False")
            self.input_listener.stopListening()

    def switchSoundChoice(self, new_text):
        return
        Krita.instance().writeSetting("BrushSfxGroup", "sound_choice", new_text)
        self.player.setSoundSource(self.__sound_options[new_text])


#Krita.instance().writeSetting("MyPluginConfigGroup", "SettingName", settingValue)
#settingValue = Krita.instance().readSetting("MyPluginConfigGroup", "SettingName", defaultValue)


Krita.instance().addDockWidgetFactory(DockWidgetFactory("brush_sfx_docker", DockWidgetFactoryBase.DockRight, BrushSFXDocker))