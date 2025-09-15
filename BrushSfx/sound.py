
import wave
import random
import math

import numpy as np
import sounddevice as sd

from .utils import clamp, lerp
from .filter import apply_filter, PeakFilter
from .input import InputListener, input_listener
from .sound_source import PenSFXSource, PencilSFXSource

class SoundPlayer:
    def __init__(self, input_data: InputListener):
        self.blocksize = 1000
        self.__sfx_source = PencilSFXSource(self.blocksize)
        self.input_data: InputListener = input_data
        

        self.play_stream = sd.OutputStream(
            samplerate=self.__sfx_source.samplerate,
            blocksize=self.blocksize,
            latency='low',
            channels=1,
            callback=self.callback
        )


    def callback(self, outdata, frames: int, cffi_time, status: sd.CallbackFlags):

        movement = self.input_data.cursor_movement
        samples = self.__sfx_source.get_samples(cffi_time, movement, self.input_data.pressure)
        outdata[:, 0] = samples[:]

    def setSoundSource(self, sound_source_class):
        self.stopPlaying()
        self.__sfx_source = sound_source_class(self.blocksize)
        self.play_stream = sd.OutputStream(
            samplerate=self.__sfx_source.samplerate,
            blocksize=self.blocksize,
            latency='low',
            channels=1,
            callback=self.callback
        )
        self.startPlaying()


    def startPlaying(self):
        self.play_stream.start()
    def stopPlaying(self):
        self.play_stream.stop()

sound_player = SoundPlayer(input_listener)