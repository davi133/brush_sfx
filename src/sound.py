import wave

import numpy as np


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
    audio_as_np_float32 = audio_as_np_int16.astype(np.float32)[0::2]

    # Normalise float32 array so that values are between -1.0 and +1.0
    max_int16 = 2 ** 15
    audio_normalised = audio_as_np_float32 / max_int16

    audio = WavObject(samplerate, audio_normalised)
    stream.close()

    return audio