import os
src_path = os.path.dirname(os.path.realpath(__file__))
plugin_root_path = src_path + "/.."
import numpy as np

def lerp(t: float, a: float, b: float):
    t = clamp(t, 0.0, 1.0)
    return a + ((b-a) * t)


def smooth_lerp(t: float, a: float, b: float):
    t = clamp(t, 0.0, 1.0)
    t = t * t * (3.0 - 2.0 * t)
    return a + ((b-a) * t)


def clamp(x: float, lower_limit: float = 0.0, upper_limit: float = 1.0) ->float:
    if x < lower_limit:
        return lower_limit
    if x > upper_limit:
        return upper_limit
    return x


def lerp_array(t: np.ndarray, a: float, b: float):
    t = np.clip(t, 0.0, 1.0)
    return a + ((b-a) * t)

def smooth_lerp_array(t: np.ndarray, a: float, b: float):
    t = np.clip(t, 0.0, 1.0)
    t = t * t * (3.0 - 2.0 * t)
    return a + ((b-a) * t)