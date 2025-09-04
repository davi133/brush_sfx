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
        for i in range(fourier.size):
            bin_frquency = abs(frequencies[i])
            if bin_frquency > self.pass_freq:
                distance_from_target = (self.cutoff - bin_frquency) / smooth
                distance_smoothed = smooth_lerp(distance_from_target, 0.0, 1.0)
                before = fourier[i]
                after = before*distance_smoothed
                fourier[i] = after

class HighPassFilter(Filter):
    def __init__(self, pass_freq, cutoff):
        self.pass_freq = pass_freq
        self.cutoff = cutoff

    def apply(self, fourier: np.ndarray, frequencies: np.ndarray):
        super().apply(fourier, frequencies)

        smooth =  self.pass_freq - self.cutoff
        for i in range(fourier.size):
            bin_frquency = abs(frequencies[i])
            if bin_frquency < self.pass_freq:
                distance_from_target = (bin_frquency - self.cutoff) / smooth
                distance_smoothed = smooth_lerp(distance_from_target, 0.0, 1.0)
                fourier[i] *= distance_smoothed

class BandPassFilter(Filter):
    def __init__(self, target_frequency, smooth):
        self.target = target_frequency
        self.smooth = smooth

    def apply(self, fourier_transformed: np.ndarray, frequencies: np.ndarray):
        super().apply(fourier_transformed, frequencies)
        raise Exception("Method not implemented")

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
        filt.apply(fourier_to_filter, frequencies_cache, False)

    samples_reconstruction = np.real(np.fft.ifft(fourier_to_filter))

    return samples_reconstruction