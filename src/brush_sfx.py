from krita import *
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout,  QCheckBox, QOpenGLWidget
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent, QTimer, QPoint
from PyQt5.QtGui import QCursor, QGuiApplication
import time
import math

import numpy as np
import sounddevice as sd

from .__init__ import src_path
from .sound import WavObject, generate_from_file


class MyExtension(Extension):

    def __init__(self, parent, value):
        super().__init__(parent)
        self.value = value

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction("sfcDebug", "Debug BSFX", "tools")
        action.triggered.connect(self.printAText)

    def printAText(self):
        print(f"the value {self.value} was successfully printed")

# And add the extension to Krita's list of extensions:
exten = MyExtension(Krita.instance(),"dasdasd")
Krita.instance().addExtension(exten)


class StrokeListener(QObject):
    def __init__(self):
        super().__init__()
        
        self.__is_pressing = False
        self.__cursor_potition = QPoint(0, 0)
        self.__last_cursor_position_read = QPoint(0, 0)
        self.__pressure = 1.0

    @property
    def is_pressing(self) -> bool:
        return self.__is_pressing
    
    @property
    def pressure(self) -> float:
        return self.__pressure
    
    @property
    def cursor_movement(self) -> float:
        movement = self.__last_cursor_position_read - self.__cursor_potition
        self.__last_cursor_position_read = self.__cursor_potition
        return movement

    def eventFilter(self, obj, event):
        if obj.__class__ != QOpenGLWidget:
            return super().eventFilter(obj, event)

        if (self.__is_pressing):
            
            #position
            if (event.type() == QEvent.TabletMove or \
                event.type() == QEvent.MouseMove):
                self.__cursor_potition = event.pos()
                    
            #pressure
            if (event.type() == QEvent.TabletMove):
                self.__preassure = event.pressure
                #print(event.pressure())

            if (event.type() == QEvent.MouseMove):
                self.__preassure = 1.0

        #pressing
        if (event.type() == QEvent.TabletPress or \
            event.type() == QEvent.MouseButtonPress) and \
            event.button()== Qt.LeftButton:
            self.__is_pressing = True
            self.__cursor_potition = event.pos()
            self.__last_cursor_position_read = event.pos()

        #releasing
        if (event.type() == QEvent.TabletRelease or \
            event.type() == QEvent.MouseButtonRelease) and \
            event.button()== Qt.LeftButton:
            self.__is_pressing = False

        #print(event.type())
        return super().eventFilter(obj, event)



class SoundPlayer:
    def __init__(self, input_data: StrokeListener):
        print("loading assets")
        self.pencil_sound_data = generate_from_file(f"{src_path}/../assets/29a-pencil.wav")

        self.input_data: StrokeListener = input_data
        self.frames_processed = 0
        self.last_callback_time = 0


        self.max_speed = 5.0 # in screens per second
        self.__window_height_px = QGuiApplication.instance().primaryScreen().size().height()
        
        self.play_stream = sd.OutputStream(
            samplerate=self.pencil_sound_data.samplerate,
            blocksize=2000,
            latency='low',
            channels=1,
            callback=self.callback
        )

        


    def callback(self, outdata, frames: int, cffi_time, status: sd.CallbackFlags):
        all_samples = self.__getSamples(frames)
        pressing_value = 1.0 if self.input_data.is_pressing else 0.0
       
        deltaTime = cffi_time.currentTime- self.last_callback_time 
        speed = self.__getSpeed(deltaTime)
            #print(cffi_time.currentTime-self.last_callback_time)
        
        all_samples *= pressing_value * speed
        outdata[:, 0] = all_samples[:]
        self.last_callback_time = cffi_time.currentTime

    def __getSamples(self, frames: int):
        samples = np.roll(self.pencil_sound_data.samples, shift=-self.frames_processed)
        self.frames_processed += frames
        return samples[:frames]
    
    def __getSpeed(self, deltaTime):
        movement = self.input_data.cursor_movement
        deltaPx = math.sqrt((movement.x() ** 2) + (movement.y() ** 2))

        screen_movement = deltaPx/self.__window_height_px
        speed = screen_movement/(deltaTime*self.max_speed)
        return speed

    def startPlaying(self):
        self.play_stream.start()
    def stopPlaying(self):
        self.play_stream.stop()


class BrushSFXDocker(DockWidget):

    def __init__(self):
        super().__init__()
        self.mainWidget = QWidget(self)
        self.setWindowTitle("Brush SFX")
    


        self.stroke_listener = StrokeListener()
        self.player = SoundPlayer(self.stroke_listener)
        self.player.startPlaying()

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 20, 0, 0)
        self.mainWidget.setLayout(self.main_layout)

        self.__is_effect_on = False
        self.SFX_checkbox = QCheckBox("SFX", self.mainWidget)
        self.SFX_checkbox.stateChanged.connect(self.switchOnOff)
        self.SFX_checkbox.setCheckState(Qt.Checked)
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

    def printEvents(self):
        print(dir(QEvent))
        


Krita.instance().addDockWidgetFactory(DockWidgetFactory("brush_sfx_docker", DockWidgetFactoryBase.DockRight, BrushSFXDocker))