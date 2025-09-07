from krita import *
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout,  QCheckBox, QOpenGLWidget, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent, QTimer, QPoint
from PyQt5.QtGui import QCursor, QGuiApplication
import time
import math

import numpy as np
import sounddevice as sd

from .__init__ import src_path, clamp, lerp
from .sound import WavObject, generate_from_file, generate_pen_noise
from .filter import LowPassFilter, apply_filter, PeakFilter

from .input import InputListener, input_listener

class SoundPlayer:
    def __init__(self, input_data: InputListener):
        print("loading assets")
        #29a-pencil9i.wav
        self.pencil_sound_data = generate_pen_noise(1, 48000)
        self.input_data: InputListener = input_data
        self.blocksize = 1000

        self.frames_processed = 0
        self.last_callback_time = 0

        self.__frequencies_cache = np.fft.fftfreq(self.blocksize*2, d=1/self.pencil_sound_data.samplerate)
        self.__zero_to_one = np.concatenate((np.linspace(start=0,stop=1, num=self.blocksize//2), np.ones(self.blocksize//2)))
        self.__zero_to_one = np.linspace(start=0,stop=1, num=self.blocksize)
        self.__samples_as_last_callback = np.zeros(self.blocksize)


        self.max_speed = 10 # in screens per second
        self.__window_height_px = QGuiApplication.instance().primaryScreen().size().height()
        
        #self.__last_speed = 0
        self.play_stream = sd.OutputStream(
            samplerate=self.pencil_sound_data.samplerate,
            blocksize=self.blocksize,
            latency='low',
            channels=1,
            callback=self.callback
        )


    def callback(self, outdata, frames: int, cffi_time, status: sd.CallbackFlags):
        all_samples = self.__getSamples(frames*2)
        pressing_value = 1.0 if self.input_data.is_pressing else 0.0   
        deltaTime = cffi_time.currentTime - self.last_callback_time 
        
        speed = self.__getSpeed(deltaTime) * self.input_data.is_pressing
        
        pressure = self.input_data.pressure
        filters =[
            #PeakFilter(750+ speed_shift, 800 +speed_shift, 820+speed_shift, 1020+speed_shift, 4 + (4*(pressure)) ),  #  800
            #PeakFilter(750, 800, 820, 1220, 8 + (4*pressure)),  #  800
            #PeakFilter(2500, 3000, 3010, 3500, 1 * ((math.cos(math.pi*pressure)+1))/2), # 3k 
            #PeakFilter(12000, 13000, 13100, 14000, 0.5 * (clamp(1-3*pressure,0.0, 1.0)) ), # 13k
            #PeakFilter(3100, 3500, 24000, 25000, 0.5 * (clamp(1-3*pressure,0.0, 1.0)) ), # highers
        ]
        if pressure > 0: print(self.frames_processed)
        all_samples *= speed *  lerp(pressure, 0.3, 1.0)
        filtered_samples = apply_filter(all_samples, self.pencil_sound_data.samplerate, self.__frequencies_cache, filters)
        #filtered_samples = all_samples
        self.__mix_samples(self.__samples_as_last_callback, filtered_samples)

        outdata[:, 0] = filtered_samples[:frames]
        self.__samples_as_last_callback = filtered_samples[frames:]
        self.last_callback_time = cffi_time.currentTime

    def __getSamples(self, frames: int):
        samples = np.roll(self.pencil_sound_data.samples, shift=-self.frames_processed)
        self.frames_processed += frames //2
        return samples[:frames]
    
    def __getSpeed(self, deltaTime):
        movement = self.input_data.cursor_movement
        deltaPx = math.sqrt((movement.x() ** 2) + (movement.y() ** 2))

        if deltaTime == 0:
            deltaTime =1
        speed_px = deltaPx/deltaTime
        speed_screen = speed_px/self.__window_height_px
        speed = speed_screen/self.max_speed
        #if self.input_data.is_pressing:
        #    print(clamp(speed, 0.0, 1.0))
        return clamp(speed, 0.0, 1.0)
    
    def __mix_samples(self, A: np.ndarray, B: np.ndarray):
        B[:self.blocksize] = (A * (1 - self.__zero_to_one)) + (B[:self.blocksize] * self.__zero_to_one)

    def startPlaying(self):
        self.play_stream.start()
    def stopPlaying(self):
        self.play_stream.stop()



class BrushSFXDocker(DockWidget):

    def __init__(self):
        super().__init__()
        self.mainWidget = QWidget(self)
        self.setWidget(self.mainWidget)
        self.setWindowTitle("Brush SFX")
        


        self.stroke_listener = input_listener
        self.player = SoundPlayer(self.stroke_listener)
        self.player.startPlaying()

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(15, 20, 0, 0)
       

        self.lowpass_checkbox = QCheckBox("lowpass", self.mainWidget)
        self.lowpass_checkbox.stateChanged.connect(self.switchLowPass)
        
        
        self.__is_effect_on = False
        self.SFX_checkbox = QCheckBox("SFX", self.mainWidget)
        self.SFX_checkbox.stateChanged.connect(self.switchOnOff)
        self.SFX_checkbox.setCheckState(Qt.Checked)
        #
        self.switchOnOff(Qt.Checked)
        
        self.mainWidget.setLayout(self.main_layout)
        self.mainWidget.layout().addWidget(self.lowpass_checkbox)
        self.mainWidget.layout().addWidget(self.SFX_checkbox)
        print("docker initialized")

    def canvasChanged(self, canvas):
        pass

    def switchOnOff(self, state):
        if state == Qt.Checked:
            print("listening")
            QApplication.instance().installEventFilter(self.stroke_listener)
        else:
            print("stop listening")
            QApplication.instance().removeEventFilter(self.stroke_listener)

    def switchLowPass(self, state):
        pass
    
    def __del__(self):
        print("closing brush sfx docker")
        self.player.stopPlaying()



Krita.instance().addDockWidgetFactory(DockWidgetFactory("brush_sfx_docker", DockWidgetFactoryBase.DockRight, BrushSFXDocker))