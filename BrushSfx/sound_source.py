

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QGuiApplication, QCursor

import math
import wave

import numpy as np

from .utils import lerp, clamp, Vector2
from .constants import dir_path, BLOCKSIZE
from .filter import apply_filter, PeakFilter
from .input import input_listener

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

    # Normalize float32 array so that values are between -1.0 and +1.0
    max_int16 = 2 ** 15
    audio_normalised = audio_as_np_float32 / max_int16

    audio = WavObject(samplerate, audio_normalised)
    stream.close()

    return audio

def generate_pen_noise(duration, frequency):
    samples = np.random.rand(int(duration * frequency))
    filters = [
        PeakFilter(-100, 0, 25000, 38000, -0.968), #reduce everything a lot
        PeakFilter(-300, 570, 980, 2800, 12),#gain on lowers
        PeakFilter(000, 100, 100, 150, 1),  # peak at 100 > 1
        PeakFilter(70, 360, 360, 460, 1.5),  # peak at 300
        PeakFilter(2500, 3000, 3010, 3500, 0.6), 
        PeakFilter(8000, 8300, 15000, 18000, -0.9),  # reduce more
    ]
    ft_freq = np.fft.fftfreq(samples.size, d=1/frequency)
    samples = apply_filter(samples, frequency, frequencies_cache=ft_freq, filters=filters)

    pencil_sound = WavObject(frequency, samples)


    return pencil_sound

class SFXSource:
    def __init__(self):
        self._samplerate = 48000
        
        self.__zero_to_one = np.linspace(start=0,stop=1, num=BLOCKSIZE)
        self.__zero_to_one = self.__zero_to_one * self.__zero_to_one * (3.0 -2.0 * self.__zero_to_one)

        self.max_speed = 12 # in screens per second
        self._window_height_px = QGuiApplication.instance().primaryScreen().size().height()
        

    def _set_samplerate(self, samplerate: float):
        self._samplerate = samplerate
    def get_samplerate(self)->int:
        return self._samplerate

    def get_samples(self, cffi_time, cursor_position, pressure) -> np.ndarray:
        return np.zeros(BLOCKSIZE)

    def _mix_samples(self, A: np.ndarray, B: np.ndarray):
        B[:BLOCKSIZE] = (A * (1 - self.__zero_to_one)) + (B[:BLOCKSIZE] * self.__zero_to_one)

    def _getSpeed(self, deltaTime, cursor_movement):
        deltaPx = math.sqrt((cursor_movement.x() ** 2) + (cursor_movement.y() ** 2))
        if deltaTime == 0:
            deltaTime =1
        speed_px = deltaPx/deltaTime
        speed_screen = speed_px/self._window_height_px
        speed = speed_screen/self.max_speed

        return clamp(speed, 0.0, 1.0)

class SilenceSfx(SFXSource):
    def __init__(self):
        super().__init__()
        self.__sound_of_silence = np.zeros(BLOCKSIZE)

    def get_samples(self, cffi_time, cursor_movement: QPoint, pressure: float) -> np.ndarray:
        return self.__sound_of_silence[:]

class EraserSfx(SFXSource):
    def __init__(self):
        super().__init__()

        self.base_sound_data = self.__generate_eraser_noise()

        self.__frames_processed = 0
        self.__last_callback_time = 0
        self.__samples_as_last_callback = np.zeros(BLOCKSIZE)


    def get_samples(self, cffi_time, cursor_movement: QPoint, pressure: float) -> np.ndarray:
        deltaTime = cffi_time.currentTime - self.__last_callback_time 
        all_samples = self.__get_samples_from_base()

        speed =  self._getSpeed(deltaTime, cursor_movement)

        all_samples *= speed * lerp(pressure, 0.7, 1.0)

        self._mix_samples(self.__samples_as_last_callback, all_samples)
        self.__samples_as_last_callback = all_samples[BLOCKSIZE:]
        self.__last_callback_time = cffi_time.currentTime
        return all_samples[:BLOCKSIZE]

    def __generate_eraser_noise(self):
        samples = np.random.rand(self.get_samplerate())
        filters = [
            PeakFilter(-100, 0, 25000, 38000, -0.968),
            PeakFilter(13000,15000,15100,17000,2),
        ]
        ft_freq = np.fft.fftfreq(samples.size, d=1/self.get_samplerate())
        samples = apply_filter(samples, self.get_samplerate(), frequencies_cache=ft_freq, filters=filters)

        pencil_sound = WavObject(self.get_samplerate(), samples)


        return pencil_sound

    def __get_samples_from_base(self):
        samples = np.roll(self.base_sound_data.samples, shift=-self.__frames_processed)
        self.__frames_processed += BLOCKSIZE
        return samples[:BLOCKSIZE*2]


class PenSFXSource(SFXSource):
    def __init__(self):
        super().__init__()

        self.base_sound_data = self.__generate_pen_noise(1, self.get_samplerate())

        self.__frames_processed = 0
        self.__last_callback_time = 0
        self.__samples_as_last_callback = np.zeros(BLOCKSIZE)

        self.__frequencies_cache = np.fft.fftfreq(BLOCKSIZE*2, d=1/self.get_samplerate())

    def get_samples(self, cffi_time, cursor_movement: QPoint, pressure: float) -> np.ndarray:
        deltaTime = cffi_time.currentTime - self.__last_callback_time 
        all_samples = self.__get_samples_from_base()

        speed =  self._getSpeed(deltaTime, cursor_movement)

        shift_by_speed = -50 + ( 100 * (speed**2))
        filters =[
            PeakFilter(650+shift_by_speed, 700+shift_by_speed, 720+shift_by_speed, 1320+shift_by_speed, 2),
            PeakFilter(650+shift_by_speed, 700+shift_by_speed, 720+shift_by_speed, 1320+shift_by_speed, 6), 
            #No, its not the same as using one PeakFilter with a bigger value
        ]
        all_samples *= speed *  lerp(pressure, 0.3, 1.0)
        filtered_samples = apply_filter(all_samples, self.get_samplerate(), self.__frequencies_cache, filters)
        self._mix_samples(self.__samples_as_last_callback, filtered_samples)

        self.__samples_as_last_callback = filtered_samples[BLOCKSIZE:]
        self.__last_callback_time = cffi_time.currentTime
        return filtered_samples[:BLOCKSIZE]

    def __generate_pen_noise(self, duration, frequency):
        samples = np.random.rand(int(duration * frequency))
        filters = [
            PeakFilter(-100, 0, 25000, 38000, -0.968), #reduce everything a lot
            PeakFilter(-300, 570, 980, 2800, 12),#gain on lowers
            PeakFilter(000, 100, 100, 150, 1),  # peak at 100 > 1
            PeakFilter(70, 360, 360, 460, 1.5),  # peak at 300
            PeakFilter(2500, 3000, 3010, 3500, 0.6), 
            PeakFilter(8000, 8300, 15000, 18000, -0.9),  # reduce more
        ]
        ft_freq = np.fft.fftfreq(samples.size, d=1/frequency)
        samples = apply_filter(samples, frequency, frequencies_cache=ft_freq, filters=filters)

        pencil_sound = WavObject(frequency, samples)


        return pencil_sound

    def __get_samples_from_base(self):
        samples = np.roll(self.base_sound_data.samples, shift=-self.__frames_processed)
        self.__frames_processed += BLOCKSIZE
        return samples[:BLOCKSIZE*2]

class PencilSFXSource(SFXSource):
    def __init__(self):
        super().__init__()

        self.base_sound_data = generate_from_file(f"{dir_path}/assets/29a-pencil.wav")
        self.base_sound_data.samples *= 1.75

        self._set_samplerate(self.base_sound_data.samplerate)

        self.__frames_processed = 0
        self.__last_callback_time = 0
        self.__samples_as_last_callback = np.zeros(BLOCKSIZE)

        self.__frequencies_cache = np.fft.fftfreq(BLOCKSIZE*2, d=1/self.get_samplerate())

    def get_samples(self, cffi_time, cursor_movement: QPoint, pressure: float) -> np.ndarray:
        deltaTime = cffi_time.currentTime - self.__last_callback_time 
        all_samples = self.__get_samples_from_base()

        speed =  self._getSpeed(deltaTime, cursor_movement)
        filters =[
            PeakFilter(200,400,1000,1700,2.5 * clamp((2*pressure-1), 0, 1))
        ]
        all_samples *= speed *  lerp(pressure, 0.3, 1.0)
        filtered_samples = apply_filter(all_samples, self.get_samplerate(), self.__frequencies_cache, filters)
        self._mix_samples(self.__samples_as_last_callback, filtered_samples)

        self.__samples_as_last_callback = filtered_samples[BLOCKSIZE:]
        self.__last_callback_time = cffi_time.currentTime
        return filtered_samples[:BLOCKSIZE]

    def __get_samples_from_base(self):
        samples = np.roll(self.base_sound_data.samples, shift=-self.__frames_processed)
        self.__frames_processed += BLOCKSIZE
        return samples[:BLOCKSIZE*2]


class PaintBrushSfx(SFXSource):
    def __init__(self):
        super().__init__()
        self.base_sound_data = self.__generate_paintbrush_noise()
        self.max_speed = 15 # in screens per second

        self.__frames_processed = 0
        self.__last_callback_time = 0
        self.__samples_as_last_callback = np.zeros(BLOCKSIZE)

        self.__frequencies_cache = np.fft.fftfreq(BLOCKSIZE*2, d=1/self.get_samplerate())

    def get_samples(self, cffi_time, cursor_movement: QPoint, pressure: float) -> np.ndarray:
        deltaTime = cffi_time.currentTime - self.__last_callback_time 
        all_samples = self.__get_samples_from_base()

        speed =  self._getSpeed(deltaTime, cursor_movement)
        speed = speed **2
        pressure = pressure **2
        filters =[]
        all_samples *= speed *  lerp(pressure, 0.1, 1.0)
        filtered_samples = apply_filter(all_samples, self.get_samplerate(), self.__frequencies_cache, filters)
        self._mix_samples(self.__samples_as_last_callback, filtered_samples)

        self.__samples_as_last_callback = filtered_samples[BLOCKSIZE:]
        self.__last_callback_time = cffi_time.currentTime
        return filtered_samples[:BLOCKSIZE]

    def __generate_paintbrush_noise(self):
        samples = np.random.rand(self.get_samplerate())
        filters = [
            PeakFilter(-100, 0, 25000, 38000, -0.83),
            PeakFilter(-100, 0, 1200, 3800, 0.5),
        ]
        ft_freq = np.fft.fftfreq(samples.size, d=1/self.get_samplerate())
        samples = apply_filter(samples, self.get_samplerate(), frequencies_cache=ft_freq, filters=filters)

        pencil_sound = WavObject(self.get_samplerate(), samples)

        return pencil_sound


    def __get_samples_from_base(self):
        samples = np.roll(self.base_sound_data.samples, shift=-self.__frames_processed)
        self.__frames_processed += BLOCKSIZE
        return samples[:BLOCKSIZE*2]

class AirbrushSfx(SFXSource):
    def __init__(self):
        super().__init__()
        self.base_sound_data = self.__generate_airbrush_noise()
        
        self.__frames_processed = 0
        self.__last_callback_time = 0
        self.__samples_as_last_callback = np.zeros(BLOCKSIZE)

        self.__frequencies_cache = np.fft.fftfreq(BLOCKSIZE*2, d=1/self.get_samplerate())

        self._frames_since_last_move = 0

    def get_samples(self, cffi_time, cursor_movement: QPoint, pressure: float) -> np.ndarray:
        deltaTime = cffi_time.currentTime - self.__last_callback_time 
        all_samples = self.__get_samples_from_base()
    
        speed =  self._getSpeed(deltaTime, cursor_movement)
        is_moving = 1 if speed > 0 else 0
        is_pressing = 1 if pressure > 0 else 0 
        is_moving_smooth = 1 if is_moving or (self._frames_since_last_move <= 3 and is_pressing) else 0
        self._frames_since_last_move = 0 if is_moving else self._frames_since_last_move + 1

        peak_pos = 12000
        peak_spread = 3500 + (7000 * pressure) 
        filters =[
            PeakFilter(peak_pos-peak_spread,peak_pos-10,peak_pos+10,peak_pos+peak_spread, 4),
        ]
        all_samples *= is_pressing * lerp(pressure, 0.45, 1.0)
        filtered_samples = apply_filter(all_samples, self.get_samplerate(), self.__frequencies_cache, filters)
        self._mix_samples(self.__samples_as_last_callback, filtered_samples)

        self.__samples_as_last_callback = filtered_samples[BLOCKSIZE:]
        self.__last_callback_time = cffi_time.currentTime
        return filtered_samples[:BLOCKSIZE]

    def __generate_airbrush_noise(self):
        samples = np.random.rand(self.get_samplerate())
        peak_pos = 13000
        peak_spread = 4000
        filters = [
            PeakFilter(-100, 0, 25000, 38000, -0.96) 
        ]
        ft_freq = np.fft.fftfreq(samples.size, d=1/self.get_samplerate())
        samples = apply_filter(samples, self.get_samplerate(), frequencies_cache=ft_freq, filters=filters)

        airbrush_sound = WavObject(self.get_samplerate(), samples)

        return airbrush_sound


    def __get_samples_from_base(self):
        samples = np.roll(self.base_sound_data.samples, shift=-self.__frames_processed)
        self.__frames_processed += BLOCKSIZE
        return samples[:BLOCKSIZE*2]


class SpraycanSfx(SFXSource):
    def __init__(self):
        super().__init__()
        self.base_sound_data = self.__generate_spray_noise()
        self.base_rattle_sound_data = self.__load_rattle_sound()
        
        self.__frames_processed = 0
        self.__rattle_frames_processed = 0
        self.__last_callback_time = 0
        self.__samples_as_last_callback = np.zeros(BLOCKSIZE)

        self.__frames_since_last_move = 0
        self.__last_qcursor_pos = QPoint(0,0)
        self.__last_cursor_speed = Vector2(0,0)
        self.__shakeness = 0.0

        self.__frequencies_cache = np.fft.fftfreq(BLOCKSIZE*2, d=1/self.get_samplerate())

    def get_samples(self, cffi_time, cursor_movement: QPoint, pressure: float) -> np.ndarray:
        deltaTime = cffi_time.currentTime - self.__last_callback_time 
        all_samples = self.__get_samples_from_base()
        rattle_samples = self.__get_samples_from_rattle_base()

        speed =  self._getSpeed(deltaTime, cursor_movement)
        is_moving = 1 if speed > 0 else 0
        is_pressing = 1 if pressure > 0 else 0 
        is_moving_smooth = 1 if is_moving or (self.__frames_since_last_move <= 3 and is_pressing) else 0
        self.__frames_since_last_move = 0 if is_moving else self.__frames_since_last_move + 1

        peak_pos = 12000
        peak_spread = 3500 + (7000 * pressure) 
        filters =[
        ]
        all_samples *= is_moving_smooth * lerp(pressure, 0.45, 1.0)
        filtered_samples = apply_filter(all_samples, self.get_samplerate(), self.__frequencies_cache, filters)
        self._mix_samples(self.__samples_as_last_callback, filtered_samples)

        self.__samples_as_last_callback = filtered_samples[BLOCKSIZE:]

        #adding rattle
        qcursor_movement = self.__last_qcursor_pos - QCursor.pos() #detecting movement even when not pressing
        speed_vector = self.__get_speed_vector(deltaTime, qcursor_movement)
        acceleration_vector = speed_vector - self.__last_cursor_speed
        defiance = self.__last_cursor_speed.dot(acceleration_vector) * -1
        self.__shakeness += clamp(defiance, 0.0, -1*(is_pressing-1)) 
        self.__shakeness = clamp(self.__shakeness, 0.0, 1.0)
        
        rattle_samples *= (self.__shakeness**2) if input_listener.is_over_canvas else 0
        filtered_samples = filtered_samples +rattle_samples

        self.__shakeness -= 2.0 * deltaTime
        self.__last_cursor_speed = speed_vector
        self.__last_qcursor_pos = QCursor.pos()
        self.__last_callback_time = cffi_time.currentTime
        return filtered_samples[:BLOCKSIZE]

    def __generate_spray_noise(self):
        samples = np.random.rand(self.get_samplerate())
        peak_pos = 12000
        peak_spread = 5000
        filters = [
            PeakFilter(-100, 0, 25000, 38000, -0.94),
            PeakFilter(peak_pos-peak_spread,peak_pos-10,peak_pos+10,peak_pos+peak_spread, 4)
        ]
        ft_freq = np.fft.fftfreq(samples.size, d=1/self.get_samplerate())
        samples = apply_filter(samples, self.get_samplerate(), frequencies_cache=ft_freq, filters=filters)

        spray_sound = WavObject(self.get_samplerate(), samples)

        return spray_sound
    
    def __load_rattle_sound(self):
        spray_record = generate_from_file(f"{dir_path}/assets/spray-paint-shake-seven-87908.wav")
        middle = spray_record.samples[12400:60000]
        spray_record.samples = middle
        return spray_record


    def __get_speed_vector(self, deltaTime, movement_qpoint):
        mov_vec = Vector2.fromQPoint(movement_qpoint)
        if deltaTime == 0:
            deltaTime =1
        speed_px = mov_vec/deltaTime
        speed_screen = speed_px/self._window_height_px
        speed = speed_screen/(self.max_speed)

        return Vector2.clamp_lenght(speed, 0.0, 1.0)

    def __get_samples_from_base(self):
        samples = np.roll(self.base_sound_data.samples, shift=-self.__frames_processed)
        self.__frames_processed += BLOCKSIZE
        return samples[:BLOCKSIZE*2]

    def __get_samples_from_rattle_base(self):
        samples = np.roll(self.base_rattle_sound_data.samples, shift=-self.__rattle_frames_processed)
        self.__rattle_frames_processed += BLOCKSIZE
        return samples[:BLOCKSIZE*2]