
from krita import *
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from PyQt5.QtCore import Qt, QObject, QEvent, QPoint, QTimer, pyqtSignal
import time

class InputListener(QObject):
    canvasClicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        self.__is_listening = False

        self.__is_pressing = False
        self.__cursor_potition = QPoint(0, 0)
        self.__last_cursor_position_read = QPoint(0, 0)
        self.__pressure = 0.0
        self.__is_tablet_input = False
        self.__last_tablet_input_time = time.time()
        self.__is_over_canvas = False
        
        self.__time_for_tablet = 0.1


    @property
    def is_listening(self):
        return self.__is_listening
        
    @property
    def is_tablet(self)-> bool:
        return self.__is_tablet_input

    @property
    def is_pressing(self) -> bool:
        return self.__is_pressing
    
    @property
    def pressure(self) -> float:
        return self.__pressure * self.__is_pressing
    
    @property
    def cursor_movement(self) -> float:
        """
        read only once per audio callback
        """
        movement = self.__last_cursor_position_read - self.__cursor_potition
        self.__last_cursor_position_read = self.__cursor_potition
        return movement

    @property
    def is_over_canvas(self) -> bool:
        return self.__is_over_canvas

    def startListening(self):
        if not self.__is_listening:
            self.__is_listening = True
            QApplication.instance().installEventFilter(self)
    
    def stopListening(self):
        if self.__is_listening:
            self.__is_listening = False
            QApplication.instance().removeEventFilter(self)

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
                self.__pressure = event.pressure()
                self.__last_tablet_input_time = time.time()
                self.__is_tablet_input = True

            if (event.type() == QEvent.MouseMove and time.time() >= self.__last_tablet_input_time + 0.1):
                self.__pressure = 1.0
                self.__is_tablet_input = False

        
        #pressing
        if (event.type() == QEvent.TabletPress or \
            event.type() == QEvent.MouseButtonPress) and \
            event.button()== Qt.LeftButton:
            self.canvasClicked.emit()
            self.__is_pressing = True
            self.__cursor_potition = event.pos()
            self.__last_cursor_position_read = event.pos()
            if event.type() == QEvent.MouseButtonPress:
                self.__pressure = 1.0

        #releasing
        if (event.type() == QEvent.TabletRelease or \
            event.type() == QEvent.MouseButtonRelease) and \
            event.button()== Qt.LeftButton:
            self.__pressure = 0.0
            self.__is_pressing = False

        return super().eventFilter(obj, event)

input_listener = InputListener()

class BrushPresetListener(QObject):
    currentPresetChanged = pyqtSignal(Resource)

    def __init__(self):
        super().__init__()
        self.__checking_interval_seconds = 1
        self.preset_timer = QTimer(self)
        self.preset_timer.setInterval(int(1000*self.__checking_interval_seconds))
        self.preset_timer.timeout.connect(self.detect_brush_preset)
        self.preset_timer.start()
        
        self.__current_preset = None

        input_listener.canvasClicked.connect(self.detect_brush_preset)

    def detect_brush_preset(self):
        current_window =Krita.instance().activeWindow()
        if current_window is None:
            return
        current_view = current_window.activeView()
        if current_view is None:
            return
        preset = current_view.currentBrushPreset()
        if preset is None:
            return

        if self.__current_preset is None:
            self.__current_preset = preset
            self.currentPresetChanged.emit(preset)
            return

        if preset.filename() != self.__current_preset.filename():
            self.currentPresetChanged.emit(preset)
        self.__current_preset = preset

    @property
    def current_preset(self):
        return self.__current_preset

brush_preset_listener = BrushPresetListener()
