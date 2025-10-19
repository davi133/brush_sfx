import math
import numpy as np
from PyQt5.QtCore import QPoint


class Vector2:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    @staticmethod
    def fromQPoint(p: QPoint):
        return Vector2(p.x(), p.y())

    def lenght(self):
        return math.sqrt((self.x ** 2) + (self.y ** 2))
    
    def dot(self, other):
        return (self.x * other.x) + (self.y * other.y)
    
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar):
        return Vector2(self.x / scalar, self.y / scalar)
    
    def normalized(self):
        return self /  self.lenght()
    
    def __str__(self):
        return f"Vector2({self.x}, {self.y})"

    @staticmethod
    def clamp_lenght(vect, lower_limit: float = 0.0, upper_limit: float = 1.0):
        lenght = vect.lenght()
        if lenght < lower_limit:
            return vect.normalized() * lower_limit
        if lenght > upper_limit:
            return vect.normalized() * upper_limit
        return vect

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

def qpoint_lenght(point: QPoint) ->float:
    return math.sqrt((point.x() ** 2) + (point.y() ** 2))
