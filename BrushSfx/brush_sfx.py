from krita import *
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QComboBox, QLabel, QDialog, QSlider
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent, QTimer, QPoint, QThread
from PyQt5.QtGui import QCursor, QGuiApplication

import time
import math
import copy
from typing import List

import numpy as np
import sounddevice as sd

from .utils import clamp, lerp
from .sound import sound_player
from .constants import DEFAULT_VOLUME, DEFAULT_SFX_ID, DEFAULT_USE_ERASER, DEFAULT_ERASER_SFX_ID, BAKING_DEFAULTS_MODE
from .sound_source import WavObject, generate_from_file, generate_pen_noise, SFXSource, \
SilenceSfx, EraserSfx, PencilSFXSource, PenSFXSource, PaintBrushSfx ,AirbrushSfx, SpraycanSfx
from .filter import LowPassFilter, apply_filter, PeakFilter
from .input import InputListener, input_listener, brush_preset_listener

from .resources import bsfxConfig, bsfxResourceRepository, kraResourceReader
 
class BrushSFXExtension(Extension):

    soundChanged = pyqtSignal(SFXSource)

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('brush_sfx_extension')

        
        
        self.input_listener = input_listener
        self.preset_listener = brush_preset_listener
        self.preset_listener.currentPresetChanged.connect(self.__onPresetChange)

        self.sound_player_thread = QThread()
        self.player = sound_player
        self.player.moveToThread(self.sound_player_thread)
        self.soundChanged.connect(self.player.setSoundSource)
        self.sound_player_thread.start()
        
        self.__sound_options = []
        self.sfx_config_in_use:bsfxConfig = bsfxConfig("", True, "",1.0)
        
        #general settings
        self.is_sfx_on = False
        self.general_sfx_config: bsfxConfig = bsfxConfig("", True, "", 0.5)
        
        #preset settings
        self.current_preset = None
        self.current_preset_id = 0
        self.is_preset_using_sfx = False
        self.preset_sfx_config: bsfxConfig = bsfxConfig("", True, "", 1.0)
        
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

        self.refreshSoundSourceOfPlayer()
        self.refreshVolumeOfPlayer()

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction("sfxConfig", "Brush SFX", "tools/scripts")
        action.triggered.connect(self.openConfig)  

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
        self.SFX_checkbox = QCheckBox("Sound Effects", self.dialogWidget)
        self.SFX_checkbox.stateChanged.connect(self.switchOnOff)
        
        # GENERAL =====================================================================================================================================
        # Volume slider
            # label
        self.volume_label = QLabel("Master volume:", self.dialogWidget)
            # slider
        self.volume_slider = VolumeSlider(self.general_sfx_config.volume, self.dialogWidget)
        self.volume_slider.volumeSliderReleased.connect(self.__volume_changed)
        self.volume_slider.setFixedWidth(310)
            # layout
        volume_layout = QVBoxLayout()
        volume_layout.addWidget(self.volume_label)
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addStretch()

        self.general_config_widget = BSfxConfigWidget(self.dialogWidget)
        self.general_config_widget.setShowVolume(False)
        self.general_config_widget.setFixedWidth(320)
        self.general_config_widget.sfxConfigChanged.connect(self.__changeGeneralConfig)

        # BRUSH PRESET =====================================================================================================================================
        self.current_preset_group = QGroupBox("Use different sound on current preset", self.dialogWidget)
        self.current_preset_group.setEnabled(False)
        self.current_preset_group.setCheckable(True)
        self.current_preset_group.setChecked(False)
        self.current_preset_group.toggled.connect(self.linkPresetWithSfx)
        
        #preset display
        self.current_preset_dispaly = QLabel("Current preset: None")

        self.current_preset_config_widget = BSfxConfigWidget(self.dialogWidget)
        self.current_preset_config_widget.setFixedWidth(290)
        self.current_preset_config_widget.sfxConfigChanged.connect(self.__changePresetConfig)

        self.current_preset_group.setLayout(QVBoxLayout())
        self.current_preset_group.layout().addWidget(self.current_preset_dispaly)
        self.current_preset_group.layout().addWidget(self.current_preset_config_widget)
        
        # =====================================================================================================================================
        self.dialogWidget.setLayout(main_layout)
        self.dialogWidget.layout().addWidget(self.SFX_checkbox)
        self.dialogWidget.layout().addLayout(volume_layout)
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
    

    ## Object __________________________________________________________________________________
    def __changeGeneralConfig(self, sfx_config):
        actual_volume = self.general_sfx_config.volume
        self.general_sfx_config = copy.deepcopy(sfx_config)
        self.general_sfx_config.volume = actual_volume

        Krita.instance().writeSetting("BrushSfx", "brush_sound", self.general_sfx_config.sfx_id)
        Krita.instance().writeSetting("BrushSfx", "use_eraser", str(self.general_sfx_config.use_eraser))
        Krita.instance().writeSetting("BrushSfx", "eraser_sound", self.general_sfx_config.eraser_sfx_id)

        self.refreshSoundSourceOfPlayer()
        self.refreshVolumeOfPlayer()

    def __changePresetConfig(self, sfx_config):
        
        self.preset_sfx_config = copy.deepcopy(sfx_config)
        if self.current_preset is not None: 
            bsfxResourceRepository.link_preset_sfx(self.current_preset_id, self.preset_sfx_config, self.current_preset.filename())
        self.refreshSoundSourceOfPlayer()
        self.refreshVolumeOfPlayer()

    ## Volume __________________________________________________________________________________

    def __volume_changed(self, volume):
        self.general_sfx_config.volume = volume
        Krita.instance().writeSetting("BrushSfx", "volume", str(int(volume*100)))
        self.refreshVolumeOfPlayer()
    
    def refreshVolumeOfPlayer(self):
        #mark refactor
        actual_volume = self.general_sfx_config.volume
        if self.is_preset_using_sfx:
            actual_volume *= self.preset_sfx_config.volume
        self.player.setVolume(actual_volume)

    ## Sound Choice ______________________________________________________________
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
        sfx_id_to_use = self.general_sfx_config.sfx_id
        if self.is_preset_using_sfx:
            sfx_id_to_use = self.preset_sfx_config.sfx_id

        sfx_to_use = self.general_sfx_config
        if self.is_preset_using_sfx:
            sfx_to_use = self.preset_sfx_config

        if self.sfx_config_in_use.sfx_id != sfx_to_use.sfx_id:
            self.sfx_config_in_use.sfx_id = sfx_to_use.sfx_id
            sfx_option = self.__getSoundChoiceById(self.sfx_config_in_use.sfx_id)
            if sfx_option is not None:
                if sfx_option["remain_cached"]:
                    if sfx_option["sound_sorce_cache"] is None:
                        sfx_option["sound_sorce_cache"] = sfx_option["sound_source_class"]()
                    self.soundChanged.emit(sfx_option["sound_sorce_cache"])
                else:
                    self.soundChanged.emit(sfx_option["sound_source_class"]())
        
        self.sfx_config_in_use.use_eraser = sfx_to_use.use_eraser
        self.player.enableUseEraser(self.sfx_config_in_use.use_eraser)

        if self.sfx_config_in_use.use_eraser and self.sfx_config_in_use.eraser_sfx_id != sfx_to_use.eraser_sfx_id:
            self.sfx_config_in_use.eraser_sfx_id = sfx_to_use.eraser_sfx_id
            sfx_option = self.__getSoundChoiceById(self.sfx_config_in_use.eraser_sfx_id)
            if sfx_option is not None:
                if sfx_option["remain_cached"]:
                    if sfx_option["sound_sorce_cache"] is None:
                        sfx_option["sound_sorce_cache"] = sfx_option["sound_source_class"]()
                    self.player.setEraserSoundSource(sfx_option["sound_sorce_cache"])
                else:
                    self.player.setEraserSoundSource(sfx_option["sound_source_class"]())
    # PRESET ________________________________________________________________________
 
    def __onPresetChange(self, preset):
        if preset is None:
            self.current_preset = None
            self.current_preset_group.setEnabled(False)
            return
        self.current_preset_dispaly.setText("Current preset: " + preset.name())
        self.current_preset_group.setEnabled(True)
        
        self.current_preset = preset
        self.current_preset_id = kraResourceReader.get_preset_id_by_filename(preset.filename())
        
        preset_sfx = bsfxResourceRepository.get_preset_sfx(self.current_preset_id)
        if BAKING_DEFAULTS_MODE:
            preset_sfx = bsfxResourceRepository.get_preset_sfx_by_filename(self.current_preset.filename())
        if preset_sfx is not None:
            self.preset_sfx_config = preset_sfx["sfx_config"]
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
            self.preset_sfx_config = copy.deepcopy(self.general_sfx_config)
            self.preset_sfx_config.volume = 1.0
            bsfxResourceRepository.link_preset_sfx(self.current_preset_id, self.preset_sfx_config, self.current_preset.filename())
            
            self.is_preset_using_sfx = True
            self.__setUIData()
        else:
            self.is_preset_using_sfx = False
            bsfxResourceRepository.unlink_preset_sfx(self.current_preset_id)
            if BAKING_DEFAULTS_MODE:
                bsfxResourceRepository.unlink_preset_sfx_by_filename(self.current_preset.filename())
            self.refreshVolumeOfPlayer()
            self.refreshSoundSourceOfPlayer()
            self.__setUIData()
    
    def __loadSettingsFromDisc(self):
        __sfx_on_setting = Krita.instance().readSetting("BrushSfx", "brush_sfx_on", "True")
        self.is_sfx_on = __sfx_on_setting != "False"

        __volume_setting = Krita.instance().readSetting("BrushSfx", "volume",  str(DEFAULT_VOLUME))
        if __volume_setting.isdigit():
            __volume_setting = clamp(int(__volume_setting), 0, 100)
        else:
            __volume_setting = DEFAULT_VOLUME
        self.general_sfx_config.volume = __volume_setting/100

        __sfx_choice_setting = Krita.instance().readSetting("BrushSfx", "brush_sound", DEFAULT_SFX_ID)
        self.general_sfx_config.sfx_id = __sfx_choice_setting

        __use_eraser_setting = Krita.instance().readSetting("BrushSfx", "use_eraser", "True")
        self.general_sfx_config.use_eraser = __use_eraser_setting != "False"

        __sfx_eraser_setting = Krita.instance().readSetting("BrushSfx", "eraser_sound", DEFAULT_ERASER_SFX_ID)
        self.general_sfx_config.eraser_sfx_id = __sfx_eraser_setting


    def __setUIData(self):
        self.volume_slider.blockSignals(True)
        self.volume_slider.setVolume(self.general_sfx_config.volume)
        self.volume_slider.blockSignals(False)

        self.SFX_checkbox.setChecked(Qt.Checked if self.is_sfx_on else Qt.Unchecked)
        self.general_config_widget.blockSignals(True)
        self.general_config_widget.setOptionsData(self.__sound_options)
        self.general_config_widget.setSfxConfig(self.general_sfx_config)
        self.general_config_widget.setEnabled(not self.is_preset_using_sfx)
        self.general_config_widget.blockSignals(False)


        self.current_preset_group.blockSignals(True)
        self.current_preset_group.setChecked(self.is_preset_using_sfx)
        self.current_preset_group.blockSignals(False)

        self.current_preset_config_widget.blockSignals(True)
        self.current_preset_config_widget.setOptionsData(self.__sound_options)
        self.current_preset_config_widget.setSfxConfig(self.preset_sfx_config)
        self.current_preset_config_widget.blockSignals(False)

    def openConfig(self):
        self.__setUIData()
        self.dialogWidget.show()     

class VolumeSlider(QWidget):
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
        self.__size_of_label = 30
        self.volume_value_label.setFixedWidth(self.__size_of_label)
        # layout
        volume_slider_layout = QHBoxLayout()
        volume_slider_layout.setContentsMargins(0, 0, 0, 0)
        volume_slider_layout.addStretch()
        volume_slider_layout.addWidget(self.volume_slider, alignment =Qt.AlignLeft)
        volume_slider_layout.addWidget(self.volume_value_label, alignment =Qt.AlignLeft)
        

        self.setLayout(volume_slider_layout)
        self.setVolume(value)

    def __value_change(self, value: int):
        volume = int(value)/100.0
        self.__volume = clamp(volume, 0.0, 1.0)
        self.__updateUI()
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
    
    def setFixedWidth(self, width: int):
        self.volume_slider.setFixedWidth(width - self.__size_of_label)
        super().setFixedWidth(width)


class BSfxConfigWidget(QWidget):
    sfxConfigChanged = pyqtSignal(bsfxConfig)

    #deprecate
    volumeChanged = pyqtSignal(float)
    soundOptionChanged = pyqtSignal(str)
    
    def __init__(self, parent):
        super().__init__(parent)
        self.__sfx_config: bsfxConfig = bsfxConfig("", False, "", 1.0)
        self.__options_data = []


        self.__show_volume = True

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        # Volume slider
            # label
        self.volume_label = QLabel("Volume:", self)
            # slider
        self.volume_slider = VolumeSlider(self.__sfx_config.volume, self)
        self.volume_slider.volumeSliderReleased.connect(self.__volume_changed)
            #layout
        volume_layout = QVBoxLayout()
        volume_layout.addWidget(self.volume_label)
        volume_layout.addWidget(self.volume_slider)

        # Brush Sound
            # label
        brush_label = QLabel("Brush sound:", self)
        brush_label.setFixedWidth(100)
            #combobox
        self.brush_sound_cb = QComboBox(self)
        self.brush_sound_cb.currentIndexChanged.connect(self.__brush_sound_changed)
            #layout
        brush_layout = QHBoxLayout()
        brush_layout.addWidget(brush_label)
        brush_layout.addWidget(self.brush_sound_cb)

        #Eraser option
        self.use_eraser_checkbox = QCheckBox("Sound for eraser", self)
        self.use_eraser_checkbox.stateChanged.connect(self.__use_eraser_checked)

        # Eraser Sound
            # label
        self.eraser_label = QLabel("Eraser sound:", self)
        self.eraser_label.setFixedWidth(100)
            #combobox
        self.eraser_sound_cb = QComboBox(self)
        self.eraser_sound_cb.currentIndexChanged.connect(self.__eraser_sound_changed)
            #layout
        eraser_layout = QHBoxLayout()
        eraser_layout.addWidget(self.eraser_label)
        eraser_layout.addWidget(self.eraser_sound_cb)

        self.layout().addLayout(volume_layout)
        self.layout().addLayout(brush_layout)
        self.layout().addWidget(self.use_eraser_checkbox)
        self.layout().addLayout(eraser_layout)

    def __volume_changed(self, volume: float):
        self.__sfx_config.volume = volume
        self.sfxConfigChanged.emit(self.__sfx_config)
        self.volumeChanged.emit(volume)
    
    def __brush_sound_changed(self, new_index):
        if new_index == -1: 
            self.__sfx_config.sfx_id = None
        if new_index >= 0 and new_index < len(self.__options_data):
            self.__sfx_config.sfx_id = self.__options_data[new_index]["sfx_id"]
        
        self.sfxConfigChanged.emit(self.__sfx_config)

    def __use_eraser_checked(self, state):
        self.__sfx_config.use_eraser = state == Qt.Checked
        self.eraser_label.setEnabled(state == Qt.Checked)
        self.eraser_sound_cb.setEnabled(state == Qt.Checked)
        self.sfxConfigChanged.emit(self.__sfx_config)

    def __eraser_sound_changed(self, new_index):
        if new_index == -1: 
            self.__sfx_config.eraser_sfx_id = None
        if new_index >= 0 and new_index < len(self.__options_data):
            self.__sfx_config.eraser_sfx_id = self.__options_data[new_index]["sfx_id"]
        self.sfxConfigChanged.emit(self.__sfx_config)

    def setOptionsData(self, options: List[dict]):
        self.__options_data = options
        self.__refreshCombobox(self.brush_sound_cb, self.__sfx_config.sfx_id)
        self.__refreshCombobox(self.eraser_sound_cb, self.__sfx_config.eraser_sfx_id)

    def setShowVolume(self, show):
        self.__show_volume = show
        self.__refreshUI()

    def setSfxConfig(self, sfx_config: bsfxConfig):
        self.__sfx_config = copy.deepcopy(sfx_config)
        self.__refreshUI()
        self.sfxConfigChanged.emit(self.__sfx_config)
    
    def setFixedWidth(self, width: int):
        super().setFixedWidth(width)
        self.volume_slider.setFixedWidth(width)

    def __refreshUI(self):
        previous_block = self.blockSignals(True)

        self.volume_label.setVisible(self.__show_volume)
        volume = self.__sfx_config.volume
        self.volume_slider.setVolume(volume)
        self.volume_slider.setVisible(self.__show_volume)
       
        brush_index = -1
        eraser_index = -1
        for i in range(len(self.__options_data)):
            if self.__sfx_config.sfx_id == self.__options_data[i]["sfx_id"]:
                brush_index = i
            if self.__sfx_config.eraser_sfx_id == self.__options_data[i]["sfx_id"]:
                eraser_index = i
        
        self.brush_sound_cb.setCurrentIndex(brush_index)
        self.eraser_sound_cb.setCurrentIndex(eraser_index)
        
        self.use_eraser_checkbox.setChecked(Qt.Checked if self.__sfx_config.use_eraser else Qt.Unchecked)
        self.eraser_label.setEnabled(self.__sfx_config.use_eraser)
        self.eraser_sound_cb.setEnabled(self.__sfx_config.use_eraser)
        
        self.blockSignals(previous_block)

    def __refreshCombobox(self, combo_box, sfx_id):
        if combo_box is None:
            return
        
        current_choices = combo_box.count()
        for i in range(current_choices)[::-1]:
            combo_box.removeItem(i)

        choice_names = [option["name"] for option in self.__options_data]
        combo_box.addItems(choice_names)
        if sfx_id in choice_names:
            combo_box.setCurrentText(sfx_id)
        else:
            combo_box.setCurrentIndex(-1)


# And add the extension to Krita's list of extensions:
exten = BrushSFXExtension(Krita.instance())
Krita.instance().addExtension(exten)
