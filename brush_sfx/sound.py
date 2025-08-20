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

def smoothstep (edge0: float, edge1: float,  x: float) -> float:
    # Scale, and clamp x to 0..1 range
    x = clamp((x - edge0) / (edge1 - edge0))

    return x * x * (3.0 - 2.0 * x)


def clamp(x: float, lower_limit: float = 0.0, upper_limit: float = 1.0) ->float:
    if x < lower_limit:
        return lower_limit
    if x > upper_limit:
        return upper_limit
    return x
