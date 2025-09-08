from PyQt5.QtGui import QGuiApplication

import wave
import random
import math

import numpy as np
import sounddevice as sd

from .__init__ import clamp, lerp
from .filter import apply_filter, PeakFilter
from .input import InputListener, input_listener

class WavObject:
    def __init__(self, samplerate: int, samples: np.ndarray):
        self.samplerate = samplerate

        self.samples = samples

def generate_from_file(path):
    stream = wave.open(path, "rb")

    samplerate = stream.getframerate()
    samples = stream.readframes(-1)

    # Convert buffer to float32 using NumPy
    audio_as_np_int16 = np.frombuffer(samples, dtype=np.int16)
    audio_as_np_float32 = audio_as_np_int16.astype(np.float32)[0::stream.getnchannels()]

    # Normalise float32 array so that values are between -1.0 and +1.0
    max_int16 = 2 ** 15
    audio_normalised = audio_as_np_float32 / max_int16

    audio = WavObject(samplerate, audio_normalised)
    stream.close()

    return audio

def generate_pen_noise(duration, frequency):
    samples = []
    for i in range(int(duration * frequency)):
        noise = (random.random() * 2) - 1.0
        samples += [noise]
    
    samples = np.array(samples)
    filters_backup1 = [
        PeakFilter(-100, 0, 25000, 38000, -0.94), #reduce everything
        PeakFilter(-300, 570, 980, 2800, 12),#gain on lowers
        PeakFilter(000, 100, 100, 150, 1),  # peak at 100 > 1
        PeakFilter(650, 800, 820, 1120,4),  # peak at 800  > 4
        PeakFilter(70, 360, 360, 460, 1.5),  # peak at 300
        PeakFilter(2500, 3000, 3010, 3500, 0.6),
        PeakFilter(8000, 8300, 15000, 18000, -0.9),  # reduce more
    ]
    filters = [
        PeakFilter(-100, 0, 25000, 38000, -0.94), #reduce everything
        PeakFilter(-300, 570, 980, 2800, 12),#gain on lowers
        PeakFilter(000, 100, 100, 150, 1),  # peak at 100 > 1
        PeakFilter(650, 700, 720, 1320,12),  # peak at 800  >2
        PeakFilter(70, 360, 360, 460, 1.5),  # peak at 300
        PeakFilter(2500, 3000, 3010, 3500, 0.6), 
        PeakFilter(8000, 8300, 15000, 18000, -0.9),  # reduce more

        
    ]

    ft_freq = np.fft.fftfreq(samples.size, d=1/frequency)
    samples = apply_filter(samples, frequency, frequencies_cache=ft_freq, filters=filters)

    max_amplitude = max(abs(samples.max()),abs(samples.min()))
    samples = samples * (0.55/max_amplitude)
    print("max é: ", max(abs(samples.max()),abs(samples.min())))

    pencil_sound = WavObject(frequency, samples)

    return pencil_sound


class SoundPlayer:
    def __init__(self, input_data: InputListener):
        print("loading assets")
        #29a-pencil9i.wav
        self.pencil_sound_data = generate_pen_noise(1, 48000)
        self.input_data: InputListener = input_data
        self.blocksize = 1000

        self.frames_processed = 0
        self.last_callback_time = 0

        self.__frequencies_cache = np.fft.fftfreq(self.blocksize*2, d=1/self.pencil_sound_data.samplerate)
        self.__zero_to_one = np.concatenate((np.linspace(start=0,stop=1, num=self.blocksize//2), np.ones(self.blocksize//2)))
        self.__zero_to_one = np.linspace(start=0,stop=1, num=self.blocksize)
        self.__samples_as_last_callback = np.zeros(self.blocksize)


        self.max_speed = 10 # in screens per second
        self.__window_height_px = QGuiApplication.instance().primaryScreen().size().height()
        
        #self.__last_speed = 0
        self.play_stream = sd.OutputStream(
            samplerate=self.pencil_sound_data.samplerate,
            blocksize=self.blocksize,
            latency='low',
            channels=1,
            callback=self.callback
        )


    def callback(self, outdata, frames: int, cffi_time, status: sd.CallbackFlags):
        all_samples = self.__getSamples(frames*2)
        pressing_value = 1.0 if self.input_data.is_pressing else 0.0   
        deltaTime = cffi_time.currentTime - self.last_callback_time 
        
        speed = self.__getSpeed(deltaTime) * self.input_data.is_pressing
        
        pressure = self.input_data.pressure
        filters =[
            #PeakFilter(750+ speed_shift, 800 +speed_shift, 820+speed_shift, 1020+speed_shift, 4 + (4*(pressure)) ),  #  800
            #PeakFilter(750, 800, 820, 1220, 8 + (4*pressure)),  #  800
            #PeakFilter(2500, 3000, 3010, 3500, 1 * ((math.cos(math.pi*pressure)+1))/2), # 3k 
            #PeakFilter(12000, 13000, 13100, 14000, 0.5 * (clamp(1-3*pressure,0.0, 1.0)) ), # 13k
            #PeakFilter(3100, 3500, 24000, 25000, 0.5 * (clamp(1-3*pressure,0.0, 1.0)) ), # highers
        ]
        if pressure > 0: print(self.frames_processed)
        all_samples *= speed *  lerp(pressure, 0.3, 1.0)
        filtered_samples = apply_filter(all_samples, self.pencil_sound_data.samplerate, self.__frequencies_cache, filters)
        #filtered_samples = all_samples
        self.__mix_samples(self.__samples_as_last_callback, filtered_samples)

        outdata[:, 0] = filtered_samples[:frames]
        self.__samples_as_last_callback = filtered_samples[frames:]
        self.last_callback_time = cffi_time.currentTime

    def __getSamples(self, frames: int):
        samples = np.roll(self.pencil_sound_data.samples, shift=-self.frames_processed)
        self.frames_processed += frames //2
        return samples[:frames]
    
    def __getSpeed(self, deltaTime):
        movement = self.input_data.cursor_movement
        deltaPx = math.sqrt((movement.x() ** 2) + (movement.y() ** 2))

        if deltaTime == 0:
            deltaTime =1
        speed_px = deltaPx/deltaTime
        speed_screen = speed_px/self.__window_height_px
        speed = speed_screen/self.max_speed
        #if self.input_data.is_pressing:
        #    print(clamp(speed, 0.0, 1.0))
        return clamp(speed, 0.0, 1.0)
    
    def __mix_samples(self, A: np.ndarray, B: np.ndarray):
        B[:self.blocksize] = (A * (1 - self.__zero_to_one)) + (B[:self.blocksize] * self.__zero_to_one)

    def startPlaying(self):
        self.play_stream.start()
    def stopPlaying(self):
        self.play_stream.stop()

sound_player = SoundPlayer(input_listener)