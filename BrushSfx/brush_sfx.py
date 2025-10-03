from krita import *
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QComboBox, QLabel, QDialog, QSlider
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent, QTimer, QPoint, QThread
from PyQt5.QtGui import QCursor, QGuiApplication
import time
import math
from typing import List

import numpy as np
import sounddevice as sd

from .utils import clamp, lerp
from .sound import sound_player
from .constants import DEFAULT_VOLUME, DEFAULT_SOUND_CHOICE
from .sound_source import WavObject, generate_from_file, generate_pen_noise, SFXSource, \
SilenceSfx, EraserSfx, PencilSFXSource, PenSFXSource, PaintBrushSfx ,AirbrushSfx, SpraycanSfx
from .filter import LowPassFilter, apply_filter, PeakFilter
from .input import InputListener, input_listener, brush_preset_listener

from .resources import bsfxResourceRepository
 
class BrushSFXExtension(Extension):

    soundChanged = pyqtSignal(SFXSource)

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('brush_sfx_extension')

        
        
        self.input_listener = input_listener
        self.preset_listener = brush_preset_listener
        self.preset_listener.currentPresetChanged.connect(self.onPresetChange)

        self.sound_player_thread = QThread()
        self.player = sound_player
        self.player.moveToThread(self.sound_player_thread)
        self.soundChanged.connect(self.player.setSoundSource)
        self.sound_player_thread.start()
        
        self.__sound_options = []
        self.sfx_in_use = ""
        
        #general settings
        self.is_sfx_on = False
        self.general_volume =0.5
        self.general_sfx_option_id = ""
        
        #preset settings
        self.current_preset = None
        self.is_preset_using_sfx = False
        self.preset_volume = 1.0
        self.preset_sfx_option_id = ""

        self.addSoundOption("bsfx_nosound", "[no sound]", SilenceSfx)
        self.addSoundOption("bsfx_eraser", "eraser", EraserSfx, remain_cached = True)
        self.addSoundOption("bsfx_pencil", "pencil", PencilSFXSource, remain_cached = True)
        self.addSoundOption("bsfx_pen", "pen", PenSFXSource, remain_cached = True)
        self.addSoundOption("bsfx_paintbrush", "paint brush", PaintBrushSfx, remain_cached = True)
        self.addSoundOption("bsfx_airbrush", "airbrush", AirbrushSfx, remain_cached = True)
        self.addSoundOption("bsfx_spraycan", "spray can", SpraycanSfx, remain_cached = True)

        self.dialogWidget = QDialog()
        self.__createDialog()
        self.__loadSettingsFromDisc()

        self.switchOnOff(self.is_sfx_on)
        self.changeGeneralVolume(self.general_volume)
        self.refreshSoundSourceOfPlayer()

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction("sfxConfig", "Brush SFX", "tools")
        action.triggered.connect(self.openConfig)

        action2 = window.createAction("sfxBrushPreset", "TestBrush", "tools")
        action2.triggered.connect(self.test_brush)
    
    import inspect
    def test_brush(self):
        print("test brush")
        fdock_dir = dir(Krita.instance().dockers()[0])
        qdock = next((w for w in Krita.instance().dockers() if w.objectName() == 'PresetDocker'), None)
        preset_dock = qdock.findChild(QWidget,'WdgPaintOpPresets')
    
    def preset_clicked(self, resource):
        print("resource")

    def addSoundOption(self, sfx_id: str, name: str, sound_source_class, remain_cached = False):
        new_sound_option = {
            "sfx_id": sfx_id,
            "name": name,
            "sound_source_class": sound_source_class,
            "sound_sorce_cache": None,
            "remain_cached": remain_cached
        }
        bsfxResourceRepository.add_sfx(sfx_id, name)
        self.__sound_options += [new_sound_option]                                                                                



    def __createDialog(self):
        self.dialogWidget.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.dialogWidget.setWindowTitle("Brush SFX")
        self.dialogWidget.setMinimumWidth(350)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 20, 15, 20)

        # CheckBox general feature
        self.SFX_checkbox = QCheckBox("SFX", self.dialogWidget)
        self.SFX_checkbox.stateChanged.connect(self.switchOnOff)
        
        self.general_config_widget = BSfxConfigWidget(self.dialogWidget)
        self.general_config_widget.setFixedWidth(320)
        self.general_config_widget.volumeChanged.connect(self.changeGeneralVolume)
        self.general_config_widget.soundOptionChanged.connect(self.changeGeneralSoundChoice)

        # BRUSH PRESET EXCLUSIVE =====================================================================================================================================
        self.current_preset_group = QGroupBox("Use different sound on current preset", self.dialogWidget)
        self.current_preset_group.setEnabled(False)
        self.current_preset_group.setCheckable(True)
        self.current_preset_group.setChecked(False)
        self.current_preset_group.toggled.connect(self.linkPresetWithSfx)
        
        #display
        self.current_preset_dispaly = QLabel("Current preset: None")

        self.current_preset_config_widget = BSfxConfigWidget(self.dialogWidget)
        self.current_preset_config_widget.setFixedWidth(290)
        self.current_preset_config_widget.volumeChanged.connect(self.changePresetVolume)
        self.current_preset_config_widget.volume_slider.volumeSliderReleased.connect(self.actuallySavePresetVolume)
        self.current_preset_config_widget.soundOptionChanged.connect(self.changePresetSoundChoice)

        self.current_preset_group.setLayout(QVBoxLayout())
        self.current_preset_group.layout().addWidget(self.current_preset_dispaly)
        self.current_preset_group.layout().addWidget(self.current_preset_config_widget)
        
        # =====================================================================================================================================
        self.dialogWidget.setLayout(main_layout)
        self.dialogWidget.layout().addWidget(self.SFX_checkbox)
        self.dialogWidget.layout().addWidget(self.general_config_widget)
        self.dialogWidget.layout().addWidget(self.current_preset_group)

    
    ## Enable and Disable Feature ______________________________________________________________
    def switchOnOff(self, state):
        if state == Qt.Checked or state == True:
            Krita.instance().writeSetting("BrushSfx", "brush_sfx_on", "True")
            self.is_sfx_on = True
            self.player.startPlaying()
            self.input_listener.startListening()
        else:
            Krita.instance().writeSetting("BrushSfx", "brush_sfx_on", "False")
            self.is_sfx_on = False
            self.player.stopPlaying()
            self.input_listener.stopListening()
    
    ## Volume __________________________________________________________________________________
    def changeGeneralVolume(self, volume):
        Krita.instance().writeSetting("BrushSfx", "volume", str(int(volume*100)))
        self.general_volume = volume
        self.refreshVolumeOfPlayer()

    def changePresetVolume(self, volume):
        if not self.is_preset_using_sfx:
            return
        self.preset_volume = volume
        self.refreshVolumeOfPlayer()
    
    def actuallySavePresetVolume(self, volume):
        if not self.is_preset_using_sfx:
            return
        self.preset_volume = volume
        bsfxResourceRepository.link_preset_sfx(
            self.current_preset.filename(),
            self.preset_sfx_option_id,
            {"volume":volume}
        )

    def refreshVolumeOfPlayer(self):
        actual_volume = self.general_volume
        if self.is_preset_using_sfx:
            actual_volume *= self.preset_volume
        self.player.setVolume(actual_volume)

    ## Sound Choice ______________________________________________________________
    
    def changeGeneralSoundChoice(self, new_choice_id):
        self.general_sfx_option_id = new_choice_id
        Krita.instance().writeSetting("BrushSfx", "sound_choice", self.general_sfx_option_id)
        self.refreshSoundSourceOfPlayer()
    
    def changePresetSoundChoice(self, new_choice_id):
        if not self.is_preset_using_sfx:
            return
        self.preset_sfx_option_id = new_choice_id
        bsfxResourceRepository.link_preset_sfx(
            self.current_preset.filename(),
            self.preset_sfx_option_id,
            {"volume":self.preset_volume}
        )
        
        self.refreshSoundSourceOfPlayer()

    
    def __getSoundChoiceById(self, sfx_id: str):
        for i in range(len(self.__sound_options)):
            if self.__sound_options[i]["sfx_id"] == sfx_id:
                return self.__sound_options[i]

    def getIndexOfSoundChoice(self, sfx_id:str):
        index = -1
        for i in range(len(self.__sound_options)):
            if self.__sound_options[i]["sfx_id"] == sfx_id:
                index = 1
        return index

    def refreshSoundSourceOfPlayer(self):
        sfx_id_to_use = self.general_sfx_option_id
        if self.is_preset_using_sfx:
            sfx_id_to_use = self.preset_sfx_option_id

        if self.sfx_in_use != sfx_id_to_use:
            self.sfx_in_use = sfx_id_to_use
            general_sfx = self.__getSoundChoiceById(self.sfx_in_use)
            if general_sfx is not None:
                if general_sfx["remain_cached"]:
                    if general_sfx["sound_sorce_cache"] is None:
                        general_sfx["sound_sorce_cache"] = general_sfx["sound_source_class"]()
                    self.soundChanged.emit(general_sfx["sound_sorce_cache"])
                else:
                    self.soundChanged.emit(general_sfx["sound_source_class"]())
    # PRESET ________________________________________________________________________
 
    def onPresetChange(self, preset):
        if preset is None:
            self.current_preset = None
            self.current_preset_group.setEnabled(False)
            return
        self.current_preset_dispaly.setText("Current preset: " + preset.name())
        self.current_preset_group.setEnabled(True)
        
        self.current_preset = preset
        preset_sfx = bsfxResourceRepository.get_preset_sfx(preset.filename())
        if preset_sfx is not None:
            self.preset_sfx_option_id = preset_sfx["sfx_id"]
            self.preset_volume = 1.0
            if preset_sfx["options"] is not None:
               self.preset_volume = preset_sfx["options"]["volume"]
            self.is_preset_using_sfx = True

            self.current_preset_group.toggled.disconnect(self.linkPresetWithSfx)
            self.current_preset_group.setChecked(True)
            self.current_preset_group.toggled.connect(self.linkPresetWithSfx)

            self.__setUIData()
        else:
            self.is_preset_using_sfx = False
            self.current_preset_group.setChecked(False)

        self.refreshVolumeOfPlayer()
        self.refreshSoundSourceOfPlayer()



    def linkPresetWithSfx(self, on):
        if on:
            bsfxResourceRepository.link_preset_sfx(
                self.current_preset.filename(), 
                self.general_sfx_option_id, 
                {"volume":1.0})
            
            self.is_preset_using_sfx = True
            self.preset_sfx_option_id = self.general_sfx_option_id
            self.preset_volume = 1.0

            self.__setUIData()
        else:
            self.is_preset_using_sfx = False
            bsfxResourceRepository.unlink_preset_sfx(self.current_preset.filename())
    
    def __loadSettingsFromDisc(self):
        __sfx_on_setting = Krita.instance().readSetting("BrushSfx", "brush_sfx_on", "True")
        self.is_sfx_on = __sfx_on_setting != "False"

        __volume_setting = Krita.instance().readSetting("BrushSfx", "volume",  str(DEFAULT_VOLUME))
        if __volume_setting.isdigit():
            __volume_setting = clamp(int(__volume_setting), 0, 100)
        else:
            __volume_setting = DEFAULT_VOLUME
        self.general_volume = __volume_setting/100

        __sfx_choice_setting = Krita.instance().readSetting("BrushSfx", "sound_choice", DEFAULT_SOUND_CHOICE)
        self.general_sfx_option_id = __sfx_choice_setting


    def __setUIData(self):
        self.SFX_checkbox.setChecked(Qt.Checked if self.is_sfx_on else Qt.Unchecked)
        self.general_config_widget.blockSignals(True)
        self.general_config_widget.soundOptionChanged.disconnect(self.changeGeneralSoundChoice)
        self.general_config_widget.setOptionsData(self.__sound_options)
        self.general_config_widget.setVolume(self.general_volume)
        self.general_config_widget.setSfxOption(self.general_sfx_option_id)
        self.general_config_widget.soundOptionChanged.connect(self.changeGeneralSoundChoice)
        self.general_config_widget.blockSignals(False)


        self.current_preset_group.blockSignals(True)
        self.current_preset_group.toggled.disconnect(self.linkPresetWithSfx)
        self.current_preset_group.setChecked(self.is_preset_using_sfx)
        self.current_preset_group.toggled.connect(self.linkPresetWithSfx)
        self.current_preset_group.blockSignals(False)

        self.current_preset_config_widget.blockSignals(True)
        self.current_preset_config_widget.setOptionsData(self.__sound_options)
        self.current_preset_config_widget.setVolume(self.preset_volume)
        self.current_preset_config_widget.setSfxOption(self.preset_sfx_option_id)
        self.current_preset_config_widget.blockSignals(False)

    def openConfig(self):
        self.__setUIData()
        self.dialogWidget.show()     

class BVolumeSlider(QWidget):
    volumeChanged = pyqtSignal(float)
    volumeSliderReleased = pyqtSignal(float)

    def __init__(self, value: float, parent):
        super().__init__(parent)
        self.__volume = 1.0

        self.volume_slider = QSlider(self)
        self.volume_slider.setTracking(False)
        self.volume_slider.setOrientation(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.valueChanged.connect(self.__value_change)
        self.volume_slider.sliderMoved.connect(self.__move_slider)
        
        # value label 
        self.volume_value_label = QLabel("100", self)
        self.volume_value_label.setFixedWidth(20)
        # layout
        volume_slider_layout = QHBoxLayout()

        volume_slider_layout.addWidget(self.volume_slider, alignment =Qt.AlignLeft)
        volume_slider_layout.addWidget(self.volume_value_label, alignment =Qt.AlignLeft)
        volume_slider_layout.setContentsMargins(0, 0, 0, 0)
        volume_slider_layout.addStretch()

        self.setLayout(volume_slider_layout)
        self.setVolume(value)

    def __value_change(self, value: int):
        volume = int(value)/100.0
        self.__volume = clamp(volume, 0.0, 1.0)
        self.volumeSliderReleased.emit(self.__volume)

    def __move_slider(self, value: int):
        volume = int(value)/100.0
        self.__volume = volume
        self.__updateUI()
        self.volumeChanged.emit(self.__volume)
    
    def __updateUI(self):
        self.volume_value_label.setText(str(int(self.__volume*100)))

    def setVolume(self, volume: float):     # for external use
        self.__volume = clamp(volume, 0.0, 1.0)
        self.volume_slider.setValue(int(self.__volume*100))
        self.__updateUI()
        self.volumeChanged.emit(self.__volume)

    def getVolume(self) -> float:
        return self.__volume
    
    def setSliderWidth(self, width: int):
        self.volume_slider.setFixedWidth(width)

class BSfxConfigWidget(QWidget):
    volumeChanged = pyqtSignal(float)
    soundOptionChanged = pyqtSignal(str)
    
    def __init__(self, parent):
        super().__init__(parent)
        self.__volume = 1.0
        self.__options_data = []
        self.__sfx_option = ""

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        # Volume slider
        # label
        volume_label = QLabel("Volume:", self)
        #volume_label.setFixedWidth(300)
        # slider
        self.volume_slider = BVolumeSlider(self.__volume, self)
        #self.volume_slider.setSliderWidth(290) #TODO rethink this size
        self.volume_slider.volumeChanged.connect(self.__volume_changed)
        #layout
        volume_layout = QVBoxLayout()
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)

        # Sound Choice
        # label
        choice_label = QLabel("Sound Choice:", self)
        choice_label.setFixedWidth(77)
        #combobox
        self.sound_choice_cb = QComboBox(self)
        self.sound_choice_cb.currentIndexChanged.connect(self.__sound_choice_changed)
        #layout
        choice_layout = QHBoxLayout()
        choice_layout.addWidget(choice_label)
        choice_layout.addWidget(self.sound_choice_cb)

        self.layout().addLayout(volume_layout)
        self.layout().addLayout(choice_layout)

    def __volume_changed(self, volume: float):
        self.volumeChanged.emit(volume)
    
    def __sound_choice_changed(self, new_index):
        if new_index == -1:
            self.soundOptionChanged.emit("None")
            return
        if new_index >= 0 and new_index < len(self.__options_data):
            self.soundOptionChanged.emit(self.__options_data[new_index]["sfx_id"])

    def setFixedWidth(self, width: int):
        super().setFixedWidth(width)
        self.volume_slider.setSliderWidth(width-30)

    def setOptionsData(self, options: List[dict]):
        self.__options_data = options
        self.__refreshComboBox()
        
    def __refreshComboBox(self):
        if self.sound_choice_cb is None:
            return
        
        current_choices = self.sound_choice_cb.count()
        for i in range(current_choices)[::-1]:
            self.sound_choice_cb.removeItem(i)

        choice_names = [option["name"] for option in self.__options_data]
        self.sound_choice_cb.addItems(choice_names)
        if self.__sfx_option in choice_names:
            self.sound_choice_cb.setCurrentText(self.__sfx_option)

    def setVolume(self, volume: float):
        self.__volume = volume
        self.volume_slider.setVolume(volume)

    def setSfxOption(self, sfx_id: str):
        index = -1
        self.__sfx_option = sfx_id
        for i in range(len(self.__options_data)):
            if sfx_id == self.__options_data[i]["sfx_id"]:
                index = i
        self.sound_choice_cb.setCurrentIndex(index)

    


# And add the extension to Krita's list of extensions:
exten = BrushSFXExtension(Krita.instance())
Krita.instance().addExtension(exten)
