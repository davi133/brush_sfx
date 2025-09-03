import wave
import random

import numpy as np

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
        PeakFilter(650, 800, 820, 1420,1),  # peak at 800  >2
        PeakFilter(70, 360, 360, 460, 1.5),  # peak at 300
        PeakFilter(2500, 3000, 3010, 3500, 0.6), 
        PeakFilter(8000, 8300, 15000, 18000, -0.9),  # reduce more

        
    ]

    ft_freq = np.fft.fftfreq(samples.size, d=1/frequency)
    samples = apply_filter(samples, frequency, frequencies_cache=ft_freq, filters=filters)

    max_amplitude = max(abs(samples.max()),abs(samples.min()))
    samples = samples * (0.25/max_amplitude)
    print("max é: ", max(abs(samples.max()),abs(samples.min())))

    pencil_sound = WavObject(frequency, samples)

    return pencil_sound