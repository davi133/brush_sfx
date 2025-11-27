from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent
from PyQt5.QtGui import QCursor, QGuiApplication, QIcon

import wave
import random
import math

import numpy as np
import sounddevice as sd

from .utils import clamp, lerp
from .constants import BLOCKSIZE
from .filter import apply_filter, PeakFilter
from .input import InputListener, input_listener, brush_preset_listener
from .sound_source import PencilSFXSource, EraserSfx
from .EKritaTools import EKritaTools, EKritaToolsId

class SoundPlayer(QObject):
    def __init__(self, input_data: InputListener):
        super().__init__()
        self.__volume = 0.0
        self.__brush_sfx_source = PencilSFXSource()
        self.__use_eraser_sfx = False
        self.__eraser_sfx_source = EraserSfx()
        self.__is_playing = False
        self.__playable_state = False
        self.__is_using_valid_tool = 0
        self.__is_using_eraser = 0
        self.input_data: InputListener = input_data
        self.device_index = -1
        

        self.allowed_tools = [
            EKritaToolsId.SVG_PATH,
            EKritaToolsId.SVG_CALLIGRAPHY,
            EKritaToolsId.PAINT_BRUSH,
            EKritaToolsId.PAINT_LINE,
            EKritaToolsId.PAINT_RECTANGLE,
            EKritaToolsId.PAINT_ELLIPSE,
            EKritaToolsId.PAINT_POLYGON,
            EKritaToolsId.PAINT_POLYLINE,
            EKritaToolsId.PAINT_PATH,
            EKritaToolsId.PAINT_PENCIL,
            EKritaToolsId.PAINT_DYNAMIC_BRUSH,
            EKritaToolsId.PAINT_MULTI_BRUSH
        ]
        EKritaTools.notifier.toolChanged.connect(self.listen_tool_change)
        brush_preset_listener.eraserModeChanged.connect(self.listen_eraser_mode)


        self.__loadDevice()
        self.play_stream = None
        self.restartStream()
        
        sd.OutputStream(
            samplerate=self.__brush_sfx_source.get_samplerate(),
            blocksize=BLOCKSIZE,
            latency='low',
            channels=1,
            callback=self.callback
        )


    def callback(self, outdata, frames: int, cffi_time, status: sd.CallbackFlags):
        movement = self.input_data.cursor_movement
        if not self.__is_using_eraser:
            samples = self.__brush_sfx_source.get_samples(cffi_time, movement, self.input_data.pressure)
        elif self.__is_using_eraser and self.__use_eraser_sfx:
            samples = self.__eraser_sfx_source.get_samples(cffi_time, movement, self.input_data.pressure)
        else:
            samples = np.zeros(BLOCKSIZE)

        exponential_volume = (math.pow(10, 3/10*self.__volume) - 1.0)
        outdata[:, 0] = samples[:] * exponential_volume * self.__is_using_valid_tool



    def setSoundSource(self, sound_source):
        previous_samplerate = self.__brush_sfx_source.get_samplerate()
        self.__brush_sfx_source = sound_source
        if previous_samplerate != self.__brush_sfx_source.get_samplerate():
            try:
                self.restartStream()
            except sd.PortAudioError as e:
                pass

    def enableUseEraser(self, enable):
        self.__use_eraser_sfx = enable

    def setEraserSoundSource(self, sound_source):
        self.__eraser_sfx_source = sound_source

    def __loadDevice(self):
        device_name = Krita.instance().readSetting("BrushSfx", "device", "default_device")
        host_name = Krita.instance().readSetting("BrushSfx", "hostapi", "default_hostapi")

        
        all_devices = sd.query_devices()
        input_devices = [device for device in all_devices if device["max_output_channels"] > 0]
        all_hosts = sd.query_hostapis()
        device_index = -1
        for device in input_devices:
            if device["name"] == device_name and all_hosts[device["hostapi"]]["name"] == host_name:
                device_index = device["index"]
                break

        if device_index != -1:
            print("device found")
            self.device_index = device_index
        else:
            print("device not found")
            self.device_index = sd.default.device[1]
            the_device = all_devices[self.device_index]
            if device_name != "default_device":
                Krita.instance().writeSetting("BrushSfx", "device", the_device["name"])
                Krita.instance().writeSetting("BrushSfx", "hostapi", all_hosts[the_device["hostapi"]]["name"])
        
        print("loaded device", device_name, host_name, self.device_index)
        
    
    def setDeviceIndex(self, index):
        all_devices = sd.query_devices()
        all_hosts = sd.query_hostapis()

        device = all_devices[index]
        if device["max_output_channels"] <= 0:
            print("[BrushSfx] Invalid device: no output channels")
            return
        
        Krita.instance().writeSetting("BrushSfx", "device", device["name"])
        Krita.instance().writeSetting("BrushSfx", "hostapi", all_hosts[device["hostapi"]]["name"])
        self.device_index = index   
        self.restartStream()  #TODO enable this bomb later

    def getDeviceIndex(self):
        return self.device_index

    def restartStream(self):
        was_playing = self.__is_playing
        was_playables = self.__playable_state

       
        try: 
            self.stopPlaying()
            sd.check_output_settings(
                device = sd.default.device,
                samplerate=self.__brush_sfx_source.get_samplerate(),
                channels=1
            )
            print("[BrushSfx] Creating audio stream")
            self.play_stream = sd.OutputStream(
                device = self.device_index,
                samplerate=self.__brush_sfx_source.get_samplerate(),
                blocksize=BLOCKSIZE,
                latency='low',
                channels=1,
                callback=self.callback
            )
            if was_playing:
                print("re start playing")
                self.startPlaying()
            self.__playable_state = True
        except sd.PortAudioError as e:
            self.__is_playing = was_playing
            self.__playable_state = False
            print("[BrushSfx] Not possible to start audio stream","is playing: " ,self.__is_playing)
            print(e.args)
            raise e

        
        

    def listen_tool_change(self, tool_id, is_checked):
        if is_checked:
            self.__is_using_valid_tool = 1 if tool_id in self.allowed_tools else 0
    
    def listen_eraser_mode(self, is_using_eraser):
        self.__is_using_eraser = 1 if is_using_eraser else 0

    def volume(self):
        return self.__volume
    
    def setVolume(self, value):
        self.__volume = clamp(value, 0.0, 1.0)
    
    def is_playing(self):
        return self.__is_playing
    def startPlaying(self):
        self.__is_playing = True
        if self.play_stream is not None:
            self.play_stream.start()
    def stopPlaying(self):
        self.__is_playing = False
        if self.play_stream is not None:
            self.play_stream.stop()

sound_player = SoundPlayer(input_listener)


class DeviceSelector(QWidget):
    deviceChanged = pyqtSignal(str)

    def __init__(self, sound_player: SoundPlayer, parent):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        #internals
        self.player = sound_player
        self.all_devices = None
        self.input_devices = None
        self.hosts = None

        #UI
        device_label = QLabel("Output Device", self)
        device_label.setFixedWidth(100)

        self.device_options = QComboBox(self)
        self.device_options.setFixedWidth(250)
        self.device_options.currentIndexChanged.connect(self.__device_selected)
        
        line_layout = QHBoxLayout()
        line_layout.addWidget(device_label)
        line_layout.addWidget(self.device_options)
            # layout
        self.layout().addLayout(line_layout)


        self.__refresh_list()


    def __device_selected(self, index):
        if index <= 0:
            self.__refresh_list()
            return

        new_device = self.input_devices[index-1]
        if self.player is not None:
            self.player.setDeviceIndex(new_device["index"])
        self.deviceChanged.emit(new_device['name'])
    first_refresh = True
    def __refresh_list(self):
        print(self.player.getDeviceIndex())
        print(sd.query_devices())

        self.all_devices = sd.query_devices()
        self.input_devices = [device for device in self.all_devices if device["max_output_channels"] > 0]
        self.hosts = sd.query_hostapis()

        for device in self.input_devices:
            device["name"] = f"{device['name']}({self.hosts[device['hostapi']]['name']})"

        options_list = ["<refresh device list>"]
        options_list +=[device['name'] for device in self.input_devices]
        self.device_options.blockSignals(True)
        if self.first_refresh:
            self.device_options.addItems(options_list)
            self.first_refresh = False

        if self.player is not None:
            player_device_index = self.player.getDeviceIndex()
            for device in self.input_devices:
                if device["index"] == player_device_index:
                    self.device_options.setCurrentText(device["name"])
        self.device_options.blockSignals(False)

        


