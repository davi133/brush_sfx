
from krita import *
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from PyQt5.QtCore import Qt, QObject, QEvent, QPoint, QTimer
import time

#You can connect to the canvasChanged signal of the active view 
#(Krita.instance().activeWindow().activeView().canvasChanged.connect(your_function)). 
#This signal fires when the canvas itself changes (e.g., zoom, pan, document change), 
#but it can also be a good trigger to re-evaluate the current brush preset or properties. 
#Within your connected function, you can then perform the checks described in points 1 and 2.

class InputListener(QObject):
    def __init__(self):
        super().__init__()
        
        self.__is_listening = False

        self.__is_pressing = False
        self.__cursor_potition = QPoint(0, 0)
        self.__last_cursor_position_read = QPoint(0, 0)
        self.__pressure = 0.0
        self.__is_tablet_input = False
        self.__last_tablet_input_time = time.time()
        
        self.__time_for_tablet = 0.1
        
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
            self.__pressure = 0.0
            self.__is_pressing = False

        return super().eventFilter(obj, event)

class BrushPresetListener(QObject):
    def __init__(self):
        super().__init__()
        self.__checking_interval_seconds = 2
        self.preset_timer = QTimer(self)
        self.preset_timer.setInterval(int(1000*self.__checking_interval_seconds))
        self.preset_timer.timeout.connect(self.detect_brush_preset)
        self.preset_timer.start()
        
        self.__preset_name = ""
    
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
        self.__preset_name = preset.name()

    @property
    def preset_name(self):
        return self.__preset_name

brush_preset_listener = BrushPresetListener()
input_listener = InputListener()