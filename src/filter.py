from typing import List

from .__init__ import clamp, smooth_lerp, smooth_lerp_array

import numpy as np

class Filter:
    def __init__(self):
        pass

    def apply(self, fourier: np.ndarray, frequencies: np.ndarray):
        if fourier.size != frequencies.size:
            raise Exception("list of frequencies doesnt match with the fourier transformation")

class LowPassFilter(Filter):
    def __init__(self, pass_freq, cutoff):
        self.pass_freq = pass_freq
        self.cutoff = cutoff

    def apply(self, fourier: np.ndarray, frequencies: np.ndarray):
        super().apply(fourier, frequencies)
        smooth =  self.cutoff - self.pass_freq
        freq_abs = np.abs(frequencies)
        distance_from_cutoff = (self.cutoff - freq_abs) / smooth
        distance_smoothed = smooth_lerp_array(distance_from_cutoff, 0.0, 1.0)
        fourier[:] *= distance_smoothed

class HighPassFilter(Filter):
    def __init__(self, pass_freq, cutoff):
        self.pass_freq = pass_freq
        self.cutoff = cutoff

    def apply(self, fourier: np.ndarray, frequencies: np.ndarray):
        super().apply(fourier, frequencies)

        smooth =  self.pass_freq - self.cutoff
        freq_abs = np.abs(frequencies)
        distance_from_cutoff = (freq_abs - self.cutoff) / smooth
        distance_smoothed = smooth_lerp(distance_from_cutoff, 0.0, 1.0)
        fourier[:] *= distance_smoothed


class PeakFilter(Filter):
    def __init__(self, lower_target, lower_smooth, higher_smooth, higher_target, gain: float = 0.0):
        self.higher_target = higher_target
        self.higher_smooth = higher_smooth
        self.lower_smooth = lower_smooth
        self.lower_target = lower_target
        if not (self.higher_target >= self.higher_smooth and \
                self.higher_smooth >= self.lower_smooth and \
                self.lower_smooth >=self.lower_target):
            raise Exception("invalid values")
        self.gain = gain

    def apply(self, fourier: np.ndarray, frequencies: np.ndarray):
        super().apply(fourier, frequencies)

        freq_abs = np.absolute(frequencies)
        distance_from_lower = (freq_abs - self.lower_target) / ((self.lower_smooth - self.lower_target) + 0.0001)
        distance_from_higer = (self.higher_target - freq_abs) / ((self.higher_target - self.higher_smooth) + 0.0001)
        distance_from_target = smooth_lerp_array(np.minimum(distance_from_lower, distance_from_higer), 0, 1)
        fourier[:] += (self.gain * fourier * distance_from_target)
        


def apply_filter(samples, samplerate, frequencies_cache, filters: List[Filter]):
    
    fourier_to_filter = np.fft.fft(samples)

    for filt in filters:
        filt.apply(fourier_to_filter, frequencies_cache)

    samples_reconstruction = np.real(np.fft.ifft(fourier_to_filter))

    return samples_reconstruction