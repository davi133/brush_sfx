from krita import *
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout,  QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent, QTimer

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
        self.__cursor_potition = None
        self.__previous_previuous_potition = None
        self.__last_movement = None
        self.__last_reading_time = None
        self.__pressure = 1.0

    @property
    def is_pressing() -> bool:
        return self.__is_pressing
    
    @property
    def pressure() -> float:
        return self.__pressure
    
    @property
    def cursor_speed() -> float:
        return 0.0

    def eventFilter(self, obj, event):
        #pressing
        if (event.type() == QEvent.TabletPress or \
            event.type() == QEvent.MouseButtonPress and \
            event.button()== Qt.LeftButton):
            self.__is_pressing = True
            print("pressed")


        #releasing
        if (event.type() == QEvent.TabletRelease or \
            event.type() == QEvent.MouseButtonRelease and \
            event.button()== Qt.LeftButton):
            self.__is_pressing = False
            print("released")

        #moving
        if (self.__is_pressing):
            
            if (event.type() == QEvent.TabletMove or \
                event.type() == QEvent.MouseMove):
                    pass

            if (event.type() == QEvent.TabletMove):
                self.__preassure = event.pressure
                print(event.pressure())

            if (event.type() == QEvent.MouseMove):
                self.__preassure = 1.0

        #print(event.type())
        return super().eventFilter(obj, event)

class SoundPlayer:
    def __init__(self, input_data: StrokeListener):
        print("loading assets")
        self.pencil_sound_data = generate_from_file(f"{src_path}/../assets/29a-pencil.wav")

        self.input_data: StrokeListener = input_data
        self.frames_processed = 0
        self.play_stream = sd.OutputStream(
            samplerate=self.pencil_sound_data.samplerate,
            blocksize=0,
            latency='low',
            channels=1,
            callback=self.callback
        )



    def callback(self, outdata, frames: int, time, status: sd.CallbackFlags):
        frames_rolled = np.roll(self.pencil_sound_data.samples, shift=-self.frames_processed)
        all_frames = frames_rolled[:frames]
        self.frames_processed += frames
        outdata[:, 0] = all_frames

    def getFrames():
        pass


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


        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 20, 0, 0)
        self.mainWidget.setLayout(self.main_layout)

        self.__is_effect_on = False
        self.SFX_checkbox = QCheckBox("SFX", self.mainWidget)
        self.SFX_checkbox.stateChanged.connect(self.switchOnOff)
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