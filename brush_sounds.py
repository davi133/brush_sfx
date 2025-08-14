from krita import *
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent, QTimer
import numpy as np
import sounddevice as sd



class MyExtension(Extension):

    def __init__(self, parent, value):
        super().__init__(parent)
        self.value = value

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction("myAction", "Test Extension", "tools")
        action.triggered.connect(self.printAText)

    def printAText(self):
        print(f"the value {self.value} was successfully printed")

# And add the extension to Krita's list of extensions:
exten = MyExtension(Krita.instance(),"dasdasd")
Krita.instance().addExtension(exten)


class StrokeListener(QObject):
    def __init__(self):
        super().__init__()

        self.is_pressing = False

    def eventFilter(self, obj, event):
        #print(dir(QEvent))
        if (event.type() == QEvent.TabletPress):
            self.is_pressing = True
            print("pressed")
        if (event.type() == QEvent.TabletRelease):
            self.is_pressing = False
            print("released")
        if (self.is_pressing and event.type()==QEvent.TabletMove):
            print(event.pressure())
        #print(event.type())
        return super().eventFilter(obj, event)

class BrushSFXDocker(DockWidget):

    def __init__(self):
        super().__init__()
        mainWidget = QWidget(self)
        self.setWindowTitle("Brush SFX")
        
        buttonExportDocument = QPushButton("Test featureaaaaaaaaaaaa", mainWidget)
        buttonExportDocument.clicked.connect(self.startListening)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 15, 0, 0)
        mainWidget.setLayout(self.main_layout)
        
        mainWidget.layout().addWidget(buttonExportDocument) 

        self.stroke_listener = StrokeListener()

        print("docker initialized")

    def canvasChanged(self, canvas):
        pass

    def startListening(self):
        duration = 5.0
        recording_loud =[]
        print(f"now playing a sound for {duration} seconds")
        
        for i in range(int(duration * 2000)):
            recording_loud.append(0.5 if i %2 ==0 else -0.5)
        np_recordin2 = np.array(recording_loud)
        sd.play(np_recordin2,  samplerate=2000)
        #QApplication.instance().installEventFilter(self.stroke_listener)

    def printEvents(self):
        print(dir(QEvent))
        


Krita.instance().addDockWidgetFactory(DockWidgetFactory("brush_sfx_docker", DockWidgetFactoryBase.DockRight, BrushSFXDocker))