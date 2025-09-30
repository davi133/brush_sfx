
import wave
import random
import math

import numpy as np
import sounddevice as sd

from .utils import clamp, lerp
from .constants import BLOCKSIZE
from .filter import apply_filter, PeakFilter
from .input import InputListener, input_listener
from .sound_source import PenSFXSource, PencilSFXSource

class SoundPlayer:
    def __init__(self, input_data: InputListener):
        self.__volume = 0.0
        self.__sfx_source = PencilSFXSource()
        self.__is_playing = False
        self.input_data: InputListener = input_data
        

        self.play_stream = sd.OutputStream(
            samplerate=self.__sfx_source.samplerate,
            blocksize=BLOCKSIZE,
            latency='low',
            channels=1,
            callback=self.callback
        )


    def callback(self, outdata, frames: int, cffi_time, status: sd.CallbackFlags):

        
        movement = self.input_data.cursor_movement
        samples = self.__sfx_source.get_samples(cffi_time, movement, self.input_data.pressure)

        exponential_volume = (math.pow(10, 3/10*self.__volume) - 1.0)

        outdata[:, 0] = samples[:] * exponential_volume

    def setSoundSource(self, sound_source):
        previous_samplerate = self.__sfx_source.get_samplerate()
        self.__sfx_source = sound_source
        if previous_samplerate != self.__sfx_source:

            was_playing = self.__is_playing
            self.stopPlaying()
            self.play_stream = sd.OutputStream(
                samplerate=self.__sfx_source.samplerate,
                blocksize=BLOCKSIZE,
                latency='low',
                channels=1,
                callback=self.callback
            )
            if was_playing:
                self.startPlaying()

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