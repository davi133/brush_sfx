

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QGuiApplication

import math
import wave

import numpy as np

from .utils import lerp, clamp
from .constants import dir_path
from .filter import apply_filter, PeakFilter

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
    samples = np.random.rand(int(duration * frequency))
    filters = [
        PeakFilter(-100, 0, 25000, 38000, -0.978), #reduce everything a lot
        PeakFilter(-300, 570, 980, 2800, 12),#gain on lowers
        PeakFilter(000, 100, 100, 150, 1),  # peak at 100 > 1
        #PeakFilter(650, 700, 720, 1320,2),  # peak at 800  >2
        PeakFilter(70, 360, 360, 460, 1.5),  # peak at 300
        PeakFilter(2500, 3000, 3010, 3500, 0.6), 
        PeakFilter(8000, 8300, 15000, 18000, -0.9),  # reduce more
        #PeakFilter(650, 700, 720, 1320, 6), 
    ]
    ft_freq = np.fft.fftfreq(samples.size, d=1/frequency)
    samples = apply_filter(samples, frequency, frequencies_cache=ft_freq, filters=filters)

    max_amplitude = max(abs(samples.max()),abs(samples.min()))
    print("max was ", max_amplitude)
    #samples = samples * (0.45/max_amplitude)

    pencil_sound = WavObject(frequency, samples)

    return pencil_sound

class SFXSource:
    def __init__(self, blocksize):
        self.blocksize = blocksize
        self.samplerate = 48000
        
        self.__zero_to_one = np.concatenate((np.linspace(start=0,stop=1, num=self.blocksize//2), np.ones(self.blocksize//2)))
        self.__zero_to_one = self.__zero_to_one * self.__zero_to_one * (3.0 -2.0 * self.__zero_to_one)
        

    def _set_samplerate(self, samplerate: float):
        self.samplerate = samplerate
    def get_samplerate(self)->int:
        return self.samplerate

    def get_samples(self, cffi_time, cursor_position, pressure) -> np.ndarray:
        return np.zeros(self.blocksize)

    def _mix_samples(self, A: np.ndarray, B: np.ndarray):
        B[:self.blocksize] = (A * (1 - self.__zero_to_one)) + (B[:self.blocksize] * self.__zero_to_one)



class PenSFXSource(SFXSource):
    def __init__(self, blocksize):
        super().__init__(blocksize)

        self.base_sound_data = generate_pen_noise(1, self.get_samplerate())
        

        self.__frames_processed = 0
        self.__last_callback_time = 0
        self.__last_cursor_position = QPoint(0, 0)
        self.__samples_as_last_callback = np.zeros(self.blocksize)

        
        
        self.__frequencies_cache = np.fft.fftfreq(self.blocksize*2, d=1/self.get_samplerate())
        self.max_speed = 10 # in screens per second
        self.__window_height_px = QGuiApplication.instance().primaryScreen().size().height()

    def get_samples(self, cffi_time, cursor_movement: QPoint, pressure: float) -> np.ndarray:
        deltaTime = cffi_time.currentTime - self.__last_callback_time 
        all_samples = self.__getSamples()

        speed =  self.__getSpeed(deltaTime, cursor_movement)
        shift_by_speed = -50 + ( 175 * (speed**2))
        filters =[
            PeakFilter(650+shift_by_speed, 700+shift_by_speed, 720+shift_by_speed, 1320+shift_by_speed,2),
            PeakFilter(650+shift_by_speed, 700+shift_by_speed, 720+shift_by_speed, 1320+shift_by_speed,6), #No, its not the same as using one PeakFilter with a bigger value
        ]
        all_samples *= speed *  lerp(pressure, 0.3, 1.0)
        filtered_samples = apply_filter(all_samples, self.get_samplerate(), self.__frequencies_cache, filters)
        self._mix_samples(self.__samples_as_last_callback, filtered_samples)

        self.__samples_as_last_callback = filtered_samples[self.blocksize:]
        self.__last_callback_time = cffi_time.currentTime
        return filtered_samples[:self.blocksize]

    def __getSamples(self):
        samples = np.roll(self.base_sound_data.samples, shift=-self.__frames_processed)
        self.__frames_processed += self.blocksize
        return samples[:self.blocksize*2]
    
    def __getSpeed(self, deltaTime, cursor_movement):
        deltaPx = math.sqrt((cursor_movement.x() ** 2) + (cursor_movement.y() ** 2))
        if deltaTime == 0:
            deltaTime =1
        speed_px = deltaPx/deltaTime
        speed_screen = speed_px/self.__window_height_px
        speed = speed_screen/self.max_speed

        return clamp(speed, 0.0, 1.0)

class PencilSFXSource(SFXSource):
    def __init__(self, blocksize):
        super().__init__(blocksize)

        self.base_sound_data = generate_from_file(f"{dir_path}/assets/29a-pencil.wav")
        self._set_samplerate(self.base_sound_data.samplerate)

        self.__frames_processed = 0
        self.__last_callback_time = 0
        self.__last_cursor_position = QPoint(0, 0)
        self.__samples_as_last_callback = np.zeros(self.blocksize)

        
        
        self.__frequencies_cache = np.fft.fftfreq(self.blocksize*2, d=1/self.get_samplerate())
        self.max_speed = 10 # in screens per second
        self.__window_height_px = QGuiApplication.instance().primaryScreen().size().height()

    def get_samples(self, cffi_time, cursor_movement: QPoint, pressure: float) -> np.ndarray:
        deltaTime = cffi_time.currentTime - self.__last_callback_time 
        all_samples = self.__getSamples()

        speed =  self.__getSpeed(deltaTime, cursor_movement)
        filters =[
            PeakFilter(200,400,1000,1700,2.5 * clamp((2*pressure-1), 0, 1))
        ]
        all_samples *= speed *  lerp(pressure, 0.3, 1.0)
        filtered_samples = apply_filter(all_samples, self.get_samplerate(), self.__frequencies_cache, filters)
        self._mix_samples(self.__samples_as_last_callback, filtered_samples)

        self.__samples_as_last_callback = filtered_samples[self.blocksize:]
        self.__last_callback_time = cffi_time.currentTime
        return filtered_samples[:self.blocksize]

    def __getSamples(self):
        samples = np.roll(self.base_sound_data.samples, shift=-self.__frames_processed)
        self.__frames_processed += self.blocksize
        return samples[:self.blocksize*2]
    
    def __getSpeed(self, deltaTime, cursor_movement):
        deltaPx = math.sqrt((cursor_movement.x() ** 2) + (cursor_movement.y() ** 2))
        if deltaTime == 0:
            deltaTime =1
        speed_px = deltaPx/deltaTime
        speed_screen = speed_px/self.__window_height_px
        speed = speed_screen/self.max_speed

        return clamp(speed, 0.0, 1.0)