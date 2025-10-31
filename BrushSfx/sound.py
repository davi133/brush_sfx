
from PyQt5.QtCore import QObject

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
        self.__is_using_valid_tool = 0
        self.__is_using_eraser = 0
        self.input_data: InputListener = input_data
        
        

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

        self.play_stream = sd.OutputStream(
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
        output = samples[:] * exponential_volume * self.__is_using_valid_tool
        max_sample = max(output.max(), abs(output.min()))
        if self.input_data.pressure >0:
            print(max_sample," stream ---------------------------------------")


        outdata[:, 0] = output

    def setSoundSource(self, sound_source):
        previous_samplerate = self.__brush_sfx_source.get_samplerate()
        self.__brush_sfx_source = sound_source
        if previous_samplerate != self.__brush_sfx_source.get_samplerate():
            self.__recreateStream()

    def enableUseEraser(self, enable):
        self.__use_eraser_sfx = enable

    def setEraserSoundSource(self, sound_source):
        self.__eraser_sfx_source = sound_source

    def __recreateStream(self):
        was_playing = self.__is_playing
        self.stopPlaying()
        self.play_stream = sd.OutputStream(
            samplerate=self.__brush_sfx_source.get_samplerate(),
            blocksize=BLOCKSIZE,
            latency='low',
            channels=1,
            callback=self.callback
        )
        if was_playing:
            self.startPlaying()

    def listen_tool_change(self, tool_id, is_checked):
        if is_checked:
            self.__is_using_valid_tool = 1 if tool_id in self.allowed_tools else 0
    
    def listen_eraser_mode(self, is_using_eraser):
        self.__is_using_eraser = 1 if is_using_eraser else 0

    def volume(self):
        return self.__volume
    
    def setVolume(self, value):
        self.__volume = clamp(value, 0.0, 1.0)

    def startPlaying(self):
        self.__is_playing = True
        self.play_stream.start()
    def stopPlaying(self):
        self.__is_playing = False
        self.play_stream.stop()

sound_player = SoundPlayer(input_listener)