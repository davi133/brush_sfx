from typing import List

from .__init__ import clamp, smooth_lerp

import numpy as np

class Filter:
    def __init__(self):
        pass

    def apply(self, fourier: np.ndarray, frequencies: np.ndarray, log=False):
        if fourier.size != frequencies.size:
            raise Exception("list of frequencies doesnt match with the fourier transformation")

class LowPassFilter(Filter):
    def __init__(self, pass_freq, cutoff):
        self.pass_freq = pass_freq
        self.cutoff = cutoff

    def apply(self, fourier: np.ndarray, frequencies: np.ndarray, log=False):
        super().apply(fourier, frequencies)
        smooth =  self.cutoff - self.pass_freq
        if log:
            print("applying filter================================")
        for i in range(fourier.size):
            bin_frquency = abs(frequencies[i])
            if bin_frquency > self.pass_freq:
                distance_from_target = (self.cutoff - bin_frquency) / smooth
                distance_smoothed = smooth_lerp(distance_from_target, 0.0, 1.0)
                before = fourier[i]
                after = before*distance_smoothed
                fourier[i] = after
                if log:
                    print(bin_frquency,": ", np.absolute(before), "filter applicable", np.absolute(after))

class HighPassFilter(Filter):
    def __init__(self, pass_freq, cutoff):
        self.pass_freq = pass_freq
        self.cutoff = cutoff

    def apply(self, fourier: np.ndarray, frequencies: np.ndarray, log=False):
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

    def apply(self, fourier_transformed: np.ndarray, frequencies: np.ndarray, log=False):
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

    def apply(self, fourier: np.ndarray, frequencies: np.ndarray, log=False):
        super().apply(fourier, frequencies)
        for i in range(fourier.size):
            bin_frequency = abs(frequencies[i])
            distance_from_target = 1.0
            if bin_frequency <= self.lower_smooth:
                distance_from_target = (bin_frequency - self.lower_target) / ((self.lower_smooth - self.lower_target) + 0.0001)
            elif bin_frequency >= self.higher_smooth:
                distance_from_target = (self.higher_target - bin_frequency) / ((self.higher_target - self.higher_smooth) + 0.0001)
            smoothed_distance = smooth_lerp(distance_from_target, 0.0, 1.0)
            fourier[i] += (self.gain * fourier[i] * smoothed_distance)


def apply_filter(samples, samplerate, frequencies_cache, filters: List[Filter], log=False):
    
    fourier_to_filter = np.fft.fft(samples)
    fourier_control = np.copy(fourier_to_filter)

    for filt in filters:
        filt.apply(fourier_to_filter, frequencies_cache, False)

    samples_reconstruction = np.real(np.fft.ifft(fourier_to_filter))

    if log:
        print("fourier")
        for i in range(samples.size):
            if fourier_control[i] != fourier_to_filter[i]:
                print(f"{i} filtered {samples[i]} {samples_reconstruction[i]}")

    
    return samples_reconstruction